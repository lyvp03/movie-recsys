from api.main import app
from fastapi.testclient import TestClient


def test_health_check_returns_ok():
    """Verify that the health check endpoint returns 200 and 'ok' status."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
