from pydantic import BaseModel, Field

class EmotionQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500, description="The natural language query describing the desired emotional feeling of the movie.")
    top_k: int = Field(default=10, ge=1, le=50, description="Number of recommendations to return")
