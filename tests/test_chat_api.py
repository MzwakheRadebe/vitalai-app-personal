import json
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_chat_stub_response():
    payload = {"prompt": "hello world"}
    r = client.post("/api/chat", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "reply" in data
    # With no configured external AI key, the route should fall back to stub
    assert "hello world" in data["reply"], data
    assert data["reply"].startswith("[stub]") or data["reply"].startswith("{"), data["reply"]