from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data.get("status") == "healthy"
    assert data.get("service") == "repo-scrapper-backend"


def test_search_empty_prompt():
    # Blank prompt par 400 Bad Request validate karein
    response = client.get("/api/v1/search?prompt=   &limit=3")
    assert response.status_code == 400
    assert "Prompt cannot be empty" in response.json()["detail"]


def test_search_valid_query():
    # Valid query par status 200 aur schema structure validate karein
    response = client.get("/api/v1/search?prompt=fastapi&limit=2")
    assert response.status_code == 200
    data = response.json()
    assert "query_used" in data
    assert "results" in data
    assert isinstance(data["results"], list)