def build_feature_text(movie) -> str:
    """Combine all text features into a single string for text representation."""
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
