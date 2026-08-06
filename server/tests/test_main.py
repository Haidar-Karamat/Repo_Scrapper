from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "repo-scrapper-backend"}


def test_invalid_github_url():
    response = client.post("/api/v1/scrape/summary", json={"repo_url": "invalid-url"})
    assert response.status_code == 400


def test_llm_context_invalid_url():
    response = client.post("/api/v1/scrape/llm-context", json={"repo_url": "invalid-url"})
    assert response.status_code == 400