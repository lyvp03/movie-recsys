import time
import google.generativeai as genai
from domain.interfaces.i_embedding_encoder import IEmbeddingEncoder
from domain.exceptions import EmbeddingServiceError, ValidationError


class GeminiEmbeddingEncoder(IEmbeddingEncoder):
    def __init__(self, api_keys: list[str], model: str = "models/gemini-embedding-2"):
        if not api_keys:
            raise ValueError("At least one API key must be provided.")
        self._keys = [k.strip() for k in api_keys if k.strip()]
        if not self._keys:
            raise ValueError("No valid API keys found.")
        self._model = model
        self._key_index = 0

    def _current_key(self) -> str:
        return self._keys[self._key_index % len(self._keys)]

    def _next_key(self):
        self._key_index += 1

    def encode(self, text: str) -> list[float]:
        if not text.strip():
            raise ValidationError("Cannot embed empty text")
        try:
            genai.configure(api_key=self._current_key())
            # We use text-embedding-004 as it's the recommended one, or gemini-embedding-2 if passed
            result = genai.embed_content(
                model=self._model,
                content=text,
                task_type="SEMANTIC_SIMILARITY",
            )
            return result["embedding"]
        except Exception as e:
            raise EmbeddingServiceError(str(e)) from e

    def encode_batch(self, texts: list[str], batch_size: int = 100) -> list[list[float]]:
        """Encode texts in batches, rotating API key every batch."""
        embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            for text in batch:
                embeddings.append(self.encode(text))
            self._next_key()
            time.sleep(0.5)  # small cooldown to prevent hitting rate limits too fast
        return embeddings
