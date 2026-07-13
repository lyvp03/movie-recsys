from typing import Protocol


class HasTextFeatures(Protocol):
    """Duck type for objects with text feature fields (Movie entity or MovieTable)."""

    genres: str
    overview: str
    cast: str
    keywords: str


def build_feature_text(movie: HasTextFeatures) -> str:
    """Combine all text features into a structured string for text representation.

    Works with both domain Movie entities and infrastructure MovieTable objects
    via structural subtyping (Protocol).
    """
    parts = []
    
    # Title is very important
    title = getattr(movie, "title", "")
    if title:
        parts.append(f"Title: {title}")
        parts.append(f"Title: {title}")  # Duplicate to increase weight
        
    if movie.genres:
        clean_genres = movie.genres.replace(",", " ")
        parts.append(f"Genre: {clean_genres}")
        parts.append(f"Genre: {clean_genres}") # Duplicate genre
        
    if movie.cast:
        clean_cast = movie.cast.replace(",", " ")
        parts.append(f"Cast: {clean_cast}")
        
    if movie.keywords:
        clean_kw = movie.keywords.replace(",", " ")
        parts.append(f"Keywords: {clean_kw}")
        parts.append(f"Keywords: {clean_kw}") # Duplicate keywords
        
    if movie.overview:
        parts.append(f"Plot: {movie.overview}")
        
    return " ".join(parts)
