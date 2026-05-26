from typing import Protocol


class HasTextFeatures(Protocol):
    """Duck type for objects with text feature fields (Movie entity or MovieTable)."""

    genres: str
    overview: str
    cast: str
    keywords: str


def build_feature_text(movie: HasTextFeatures) -> str:
    """Combine all text features into a single string for text representation.

    Works with both domain Movie entities and infrastructure MovieTable objects
    via structural subtyping (Protocol).
    """
    parts = []
    if movie.genres:
        parts.append(movie.genres.replace(",", " "))
    if movie.overview:
        parts.append(movie.overview)
    if movie.cast:
        parts.append(movie.cast.replace(",", " "))
    if movie.keywords:
        parts.append(movie.keywords.replace(",", " "))
    return " ".join(parts)
