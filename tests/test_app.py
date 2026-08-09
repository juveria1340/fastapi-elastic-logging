import json
import os

from fastapi.testclient import TestClient

from fastapi_elk_app import app

client = TestClient(app)
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs", "app.log")


def _log_lines():
    with open(LOG_PATH) as f:
        return [json.loads(line) for line in f if line.strip()]


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_create_user():
    response = client.post("/users", json={"name": "Alice", "email": "alice@example.com"})
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Alice"
    assert body["email"] == "alice@example.com"
    assert "id" in body


def test_get_user_found():
    response = client.get("/users/alice")
    assert response.status_code == 200
    assert response.json()["id"] == "alice"


def test_get_user_not_found():
    response = client.get("/users/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_post_job():
    payload = {"title": "DevOps Engineer", "company": "TechCorp", "location": "Remote"}
    response = client.post("/jobs", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == payload["title"]
    assert body["company"] == payload["company"]
    assert body["location"] == payload["location"]
    assert "id" in body


def test_list_jobs():
    response = client.get("/jobs")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 3
    assert all("title" in job for job in body)


def test_requests_produce_structured_json_logs():
    """The whole point of this app is structured logging - verify each
    request actually writes a parsable JSON line with the right fields."""
    response = client.get("/health")
    assert response.status_code == 200

    lines = _log_lines()
    assert any(
        line.get("message") == "Health check called" and line.get("endpoint") == "/health"
        for line in lines
    )
