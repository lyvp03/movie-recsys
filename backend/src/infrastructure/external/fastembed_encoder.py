from fastembed import TextEmbedding
from domain.interfaces.i_embedding_encoder import IEmbeddingEncoder
from domain.exceptions import EmbeddingServiceError

class FastEmbedEncoder(IEmbeddingEncoder):
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        try:
            import os
            os.makedirs("data/models", exist_ok=True)
            # Initialize the model (will download weights if not cached)
            # Use a local cache_dir to avoid Windows Temp folder corruption
            self._model = TextEmbedding(model_name=model_name, cache_dir="data/models")
            self.model_name = model_name
        except Exception as e:
            raise EmbeddingServiceError(f"Failed to initialize FastEmbed model '{model_name}': {e}") from e

    def encode(self, text: str) -> list[float]:
        try:
            # fastembed encode returns an iterator/generator of numpy arrays
            # We want the first (and only) embedding as a list of floats
            embeddings = list(self._model.embed([text]))
            if not embeddings:
                raise EmbeddingServiceError("Model returned empty embedding")
                
            # Convert the numpy array to list of floats
            return embeddings[0].tolist()
        except Exception as e:
            raise EmbeddingServiceError(f"FastEmbed encoding failed: {e}") from e

    def encode_batch(self, texts: list[str], batch_size: int = 256) -> list[list[float]]:
        try:
            # fastembed handles internal batching, but we can pass our texts directly
            embeddings_generator = self._model.embed(texts, batch_size=batch_size)
            # Convert all numpy arrays in generator to lists of floats
            return [emb.tolist() for emb in embeddings_generator]
        except Exception as e:
            raise EmbeddingServiceError(f"FastEmbed batch encoding failed: {e}") from e
