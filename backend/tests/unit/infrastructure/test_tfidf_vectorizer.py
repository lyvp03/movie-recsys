import pytest
from pathlib import Path

from infrastructure.ml.tfidf_vectorizer import TFIDFVectorizerWrapper
from domain.exceptions import DomainError


@pytest.fixture
def sample_texts():
    return [
        "Action Comedy movie about space",
        "Romantic Comedy with a happy ending",
        "Action thriller in space",
        "Sci-Fi movie space aliens",
    ]


@pytest.fixture
def vectorizer():
    # Use small max_features for testing
    return TFIDFVectorizerWrapper(max_features=10)


def test_fit_transform_shape(vectorizer, sample_texts):
    vectorizer.fit(sample_texts)
    
    dim = vectorizer.get_feature_dim()
    assert dim > 0
    assert dim <= 10  # Because max_features=10
    
    vectors = vectorizer.transform(["Comedy space"])
    assert len(vectors) == 1
    assert len(vectors[0]) == dim


def test_transform_without_fit(vectorizer):
    with pytest.raises(DomainError, match="Vectorizer has not been fitted yet"):
        vectorizer.transform(["Comedy space"])


def test_get_dim_without_fit(vectorizer):
    with pytest.raises(DomainError, match="Vectorizer has not been fitted yet"):
        vectorizer.get_feature_dim()


def test_save_and_load(vectorizer, sample_texts, tmp_path):
    vectorizer.fit(sample_texts)
    dim_before = vectorizer.get_feature_dim()
    vectors_before = vectorizer.transform(["Action space"])
    
    save_path = tmp_path / "tfidf.joblib"
    vectorizer.save(save_path)
    assert save_path.exists()
    
    new_vectorizer = TFIDFVectorizerWrapper()
    new_vectorizer.load(save_path)
    
    dim_after = new_vectorizer.get_feature_dim()
    vectors_after = new_vectorizer.transform(["Action space"])
    
    assert dim_before == dim_after
    assert vectors_before == vectors_after


def test_transform_empty_text(vectorizer, sample_texts):
    vectorizer.fit(sample_texts)
    vectors = vectorizer.transform(["", "   "])
    assert len(vectors) == 2
    assert all(v == 0.0 for v in vectors[0])  # All zeros for empty string
    assert all(v == 0.0 for v in vectors[1])
