from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_appointments_crud_and_conflicts():
    # Create base appointment A
    appt_a = {
        "patient_name": "Jane Doe",
        "clinician": "Dr. Smith",
        "starts_at": "2025-10-13T09:00:00Z",
        "ends_at": "2025-10-13T09:30:00Z",
    }
    r = client.post("/api/appointments", json=appt_a)
    assert r.status_code == 200, r.text
    a = r.json()
    a_id = a["id"]

    # Attempt overlapping appointment B for same clinician -> expect 409
    appt_b = {
        "patient_name": "John Roe",
        "clinician": "Dr. Smith",
        "starts_at": "2025-10-13T09:15:00Z",
        "ends_at": "2025-10-13T09:45:00Z",
    }
    r = client.post("/api/appointments", json=appt_b)
    assert r.status_code == 409, r.text

    # Create non-overlapping appointment C
    appt_c = {
        "patient_name": "Alice",
        "clinician": "Dr. Smith",
        "starts_at": "2025-10-13T10:00:00Z",
        "ends_at": "2025-10-13T10:30:00Z",
    }
    r = client.post("/api/appointments", json=appt_c)
    assert r.status_code == 200, r.text
    c = r.json()
    c_id = c["id"]

    # Read C
    r = client.get(f"/api/appointments/id/{c_id}")
    assert r.status_code == 200
    got_c = r.json()
    assert got_c["patient_name"] == appt_c["patient_name"]

    # Update C to overlap with A -> expect 409
    update_c_overlap = {"starts_at": "2025-10-13T09:15:00Z", "ends_at": "2025-10-13T09:45:00Z"}
    r = client.put(f"/api/appointments/id/{c_id}", json=update_c_overlap)
    assert r.status_code == 409, r.text

    # List appointments
    r = client.get("/api/appointments", params={"clinician": "Dr. Smith", "limit": 10, "offset": 0})
    assert r.status_code == 200
    listed = r.json()
    ids = [item["id"] for item in listed]
    assert a_id in ids and c_id in ids

    # Delete A and C
    r = client.delete(f"/api/appointments/id/{a_id}")
    assert r.status_code == 200
    r = client.delete(f"/api/appointments/id/{c_id}")
    assert r.status_code == 200

    # Ensure deleted
    r = client.get(f"/api/appointments/id/{a_id}")
    assert r.status_code == 404
    r = client.get(f"/api/appointments/id/{c_id}")
    assert r.status_code == 404