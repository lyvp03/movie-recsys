import pytest
from infrastructure.external.fastembed_encoder import FastEmbedEncoder
from domain.exceptions import EmbeddingServiceError

def test_fastembed_encoder_encode():
    encoder = FastEmbedEncoder()
    text = "Action movie with lots of explosions"
    vector = encoder.encode(text)
    
    # BAAI/bge-base-en-v1.5 should return 768 dimensions
    assert len(vector) == 768
    assert all(isinstance(v, float) for v in vector)

def test_fastembed_encoder_encode_batch():
    encoder = FastEmbedEncoder()
    texts = ["Action movie", "Romantic comedy"]
    vectors = encoder.encode_batch(texts)
    
    assert len(vectors) == 2
    assert len(vectors[0]) == 768
    assert len(vectors[1]) == 768
