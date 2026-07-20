from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "total_requests" in response.json()


def test_chat_flow():
    response = client.post("/chat", json={"session_id": "test-session", "message": "What are your AI solution prices?"})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert data["agent"] in ["sales", "technical", "documentation", "meeting"]


def test_reset_session():
    response = client.post("/reset-session", json={"session_id": "test-session"})
    assert response.status_code == 200
    assert response.json()["status"] == "reset"


def test_chat_empty_message():
    response = client.post("/chat", json={"session_id": "test-session-2", "message": ""})
    assert response.status_code == 400
