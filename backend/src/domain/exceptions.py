class DomainError(Exception):
    """Base domain exception."""

    pass


class EntityNotFoundError(DomainError):
    """Raised when a requested entity is not found."""

    pass


class InvalidEntityError(DomainError):
    """Raised when an entity fails domain validation rules."""

    pass


class ValidationError(DomainError):
    """Raised when an entity's data is invalid."""
    pass


class EmbeddingServiceError(DomainError):
    """Raised when the embedding service (Gemini) returns an unexpected error."""
    pass
