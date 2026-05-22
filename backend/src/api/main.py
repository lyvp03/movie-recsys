import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from qdrant_client import QdrantClient

from api.routers import recommendations


from infrastructure.ml.custom_svd_model import CustomSVDModel

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    if qdrant_url and qdrant_api_key:
        app.state.qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    else:
        # Fallback for tests/local without auth
        app.state.qdrant_client = QdrantClient(location=":memory:")
        
    app.state.cf_model = CustomSVDModel()
        
    yield
    
    # Shutdown
    if hasattr(app.state, "qdrant_client"):
        app.state.qdrant_client.close()


app = FastAPI(
    title="Movie RecSys API",
    description="Hexagonal Clean Architecture Movie Recommendation System API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(recommendations.router)

@app.get("/health")
def health_check() -> dict[str, str]:
    """Basic health check endpoint."""
    return {"status": "ok"}

