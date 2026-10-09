from fastapi.testclient import TestClient
from app.main import app

def test_health():
    response = TestClient(app).get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_reject_non_tiktok_url():
    response = TestClient(app).post("/api/videos", json={"url": "https://example.com/video/123"})
    assert response.status_code == 400
