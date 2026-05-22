import pytest
from unittest.mock import Mock, MagicMock

from qdrant_client.models import PointStruct, ScoredPoint, Record

from domain.interfaces.i_vector_store import SearchResult
from domain.exceptions import DomainError
from infrastructure.vector.qdrant_vector_store import QdrantVectorStore


@pytest.fixture
def mock_qdrant_client():
    return MagicMock()


@pytest.fixture
def vector_store(mock_qdrant_client):
    return QdrantVectorStore(mock_qdrant_client)


def test_upsert_success(vector_store, mock_qdrant_client):
    vector_store.upsert("test_col", 1, [0.1, 0.2], {"title": "Test"})
    mock_qdrant_client.upsert.assert_called_once_with(
        collection_name="test_col",
        points=[PointStruct(id=1, vector=[0.1, 0.2], payload={"title": "Test"})]
    )


def test_upsert_error(vector_store, mock_qdrant_client):
    mock_qdrant_client.upsert.side_effect = Exception("Connection error")
    with pytest.raises(DomainError, match="Failed to upsert to Qdrant: Connection error"):
        vector_store.upsert("test_col", 1, [0.1], {})


def test_search_success(vector_store, mock_qdrant_client):
    # Mocking ScoredPoint objects returned by query_points
    mock_hits = [
        ScoredPoint(id=1, version=1, score=0.9, payload={"title": "A"}),
        ScoredPoint(id=2, version=1, score=0.8, payload={"title": "B"})
    ]
    mock_qdrant_client.query_points.return_value = mock_hits
    
    results = vector_store.search("test_col", [0.1, 0.2], top_k=2)
    
    mock_qdrant_client.query_points.assert_called_once_with(
        collection_name="test_col",
        query=[0.1, 0.2],
        limit=2
    )
    
    assert len(results) == 2
    assert isinstance(results[0], SearchResult)
    assert results[0].id == 1
    assert results[0].score == 0.9
    assert results[0].payload == {"title": "A"}


def test_search_error(vector_store, mock_qdrant_client):
    mock_qdrant_client.query_points.side_effect = Exception("Search failed")
    with pytest.raises(DomainError, match="Failed to search in Qdrant: Search failed"):
        vector_store.search("test_col", [0.1], 5)


def test_delete_success(vector_store, mock_qdrant_client):
    vector_store.delete("test_col", 1)
    mock_qdrant_client.delete.assert_called_once_with(
        collection_name="test_col",
        points_selector=[1]
    )


def test_delete_error(vector_store, mock_qdrant_client):
    mock_qdrant_client.delete.side_effect = Exception("Delete failed")
    with pytest.raises(DomainError, match="Failed to delete from Qdrant: Delete failed"):
        vector_store.delete("test_col", 1)


def test_get_vector_success(vector_store, mock_qdrant_client):
    mock_record = Record(id=1, payload={}, vector=[0.5, 0.6])
    mock_qdrant_client.retrieve.return_value = [mock_record]
    
    vector = vector_store.get_vector("test_col", 1)
    
    mock_qdrant_client.retrieve.assert_called_once_with(
        collection_name="test_col",
        ids=[1],
        with_vectors=True
    )
    assert vector == [0.5, 0.6]


def test_get_vector_not_found(vector_store, mock_qdrant_client):
    mock_qdrant_client.retrieve.return_value = []
    with pytest.raises(DomainError, match="Point 1 not found in collection test_col"):
        vector_store.get_vector("test_col", 1)


def test_get_vector_no_vector(vector_store, mock_qdrant_client):
    mock_record = Record(id=1, payload={}, vector=None)
    mock_qdrant_client.retrieve.return_value = [mock_record]
    with pytest.raises(DomainError, match="Point 1 has no vector"):
        vector_store.get_vector("test_col", 1)


def test_get_vector_error(vector_store, mock_qdrant_client):
    mock_qdrant_client.retrieve.side_effect = Exception("Retrieve failed")
    with pytest.raises(DomainError, match="Failed to retrieve vector from Qdrant: Retrieve failed"):
        vector_store.get_vector("test_col", 1)
