import pytest
from unittest.mock import patch, MagicMock

from domain.exceptions import EmbeddingServiceError, ValidationError
from infrastructure.external.gemini_embedding_encoder import GeminiEmbeddingEncoder


def test_encode_returns_768_dims():
    encoder = GeminiEmbeddingEncoder(api_keys=["fake_key"])
    
    with patch("google.generativeai.embed_content") as mock_embed:
        mock_embed.return_value = {"embedding": [0.1] * 768}
        
        result = encoder.encode("Test text")
        
        assert len(result) == 768
        mock_embed.assert_called_once()
        assert mock_embed.call_args[1]["content"] == "Test text"


def test_encode_empty_text():
    encoder = GeminiEmbeddingEncoder(api_keys=["fake_key"])
    
    with pytest.raises(ValidationError, match="Cannot embed empty text"):
        encoder.encode("   ")


def test_encode_api_error():
    encoder = GeminiEmbeddingEncoder(api_keys=["fake_key"])
    
    with patch("google.generativeai.embed_content") as mock_embed:
        mock_embed.side_effect = Exception("API Quota Exceeded")
        
        with pytest.raises(EmbeddingServiceError, match="API Quota Exceeded"):
            encoder.encode("Test text")


def test_encode_batch_rotates_keys():
    encoder = GeminiEmbeddingEncoder(api_keys=["key1", "key2", "key3"])
    
    # Track which keys are used
    used_keys = []
    
    def mock_configure(api_key):
        used_keys.append(api_key)
        
    with patch("google.generativeai.configure", side_effect=mock_configure):
        with patch("google.generativeai.embed_content") as mock_embed:
            mock_embed.return_value = {"embedding": [0.1] * 768}
            
            texts = ["T1", "T2", "T3", "T4", "T5"]
            # batch_size=2 will result in 3 batches:
            # Batch 1: ["T1", "T2"] -> uses key1 twice
            # Batch 2: ["T3", "T4"] -> uses key2 twice
            # Batch 3: ["T5"] -> uses key3 once
            
            encoder.encode_batch(texts, batch_size=2)
            
            assert used_keys == ["key1", "key1", "key2", "key2", "key3"]
            
            # encode_batch should return 5 embeddings
            assert mock_embed.call_count == 5


def test_no_keys_provided():
    with pytest.raises(ValueError, match="At least one API key must be provided"):
        GeminiEmbeddingEncoder(api_keys=[])
