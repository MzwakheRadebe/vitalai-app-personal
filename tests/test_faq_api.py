from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_faq_crud_flow():
    # Create
    create_payload = {"question": "What are your business hours?", "answer": "9am-5pm"}
    r = client.post("/api/faq", json=create_payload)
    assert r.status_code == 200, r.text
    created = r.json()
    assert created["id"] > 0
    faq_id = created["id"]

    # Read
    r = client.get(f"/api/faq/id/{faq_id}")
    assert r.status_code == 200
    got = r.json()
    assert got["question"] == create_payload["question"]

    # Update
    update_payload = {"answer": "We are open Monday to Friday, 9am–5pm."}
    r = client.put(f"/api/faq/id/{faq_id}", json=update_payload)
    assert r.status_code == 200, r.text
    updated = r.json()
    assert updated["answer"] == update_payload["answer"]

    # List
    r = client.get("/api/faq", params={"q": "hours", "limit": 5, "offset": 0})
    assert r.status_code == 200
    listed = r.json()
    assert any(item["id"] == faq_id for item in listed)

    # Delete
    r = client.delete(f"/api/faq/id/{faq_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "deleted"

    # Ensure deleted
    r = client.get(f"/api/faq/id/{faq_id}")
    assert r.status_code == 404