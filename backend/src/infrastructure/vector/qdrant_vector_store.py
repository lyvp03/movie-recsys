from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct

from domain.interfaces.i_vector_store import IVectorStore, SearchResult
from domain.exceptions import DomainError


class QdrantVectorStore(IVectorStore):
    def __init__(self, client: QdrantClient):
        self._client = client

    def upsert(self, collection: str, id: int, vector: list[float], payload: dict) -> None:
        try:
            self._client.upsert(
                collection_name=collection,
                points=[
                    PointStruct(
                        id=id,
                        vector=vector,
                        payload=payload,
                    )
                ],
            )
        except Exception as e:
            raise DomainError(f"Failed to upsert to Qdrant: {str(e)}")

    def search(self, collection: str, vector: list[float], top_k: int) -> list[SearchResult]:
        try:
            hits = self._client.query_points(
                collection_name=collection,
                query=vector,
                limit=top_k,
            )
            # Support both qdrant-client < 1.9.0 and >= 1.9.0 where points/query_points return different objects
            # In latest versions, it returns a list of ScoredPoint objects.
            # ScoredPoint has .id, .score, .payload
            results = []
            
            # The returned object could be a list or an object with .points. We handle both.
            points = hits.points if hasattr(hits, "points") else hits
            
            for hit in points:
                results.append(
                    SearchResult(
                        id=int(hit.id),
                        score=float(hit.score),
                        payload=hit.payload or {},
                    )
                )
            return results
        except Exception as e:
            raise DomainError(f"Failed to search in Qdrant: {str(e)}")

    def delete(self, collection: str, id: int) -> None:
        try:
            self._client.delete(
                collection_name=collection,
                points_selector=[id],
            )
        except Exception as e:
            raise DomainError(f"Failed to delete from Qdrant: {str(e)}")

    def get_vector(self, collection: str, id: int) -> list[float]:
        try:
            records = self._client.retrieve(
                collection_name=collection,
                ids=[id],
                with_vectors=True,
            )
            if not records:
                raise DomainError(f"Point {id} not found in collection {collection}")
            
            record = records[0]
            if record.vector is None:
                raise DomainError(f"Point {id} has no vector")
                
            # Vector can be a list or a dict (if using named vectors). We assume unnamed vectors (list)
            return list(record.vector)
        except DomainError:
            raise
        except Exception as e:
            raise DomainError(f"Failed to retrieve vector from Qdrant: {str(e)}")
