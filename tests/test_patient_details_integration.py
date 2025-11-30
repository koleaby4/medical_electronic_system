import re

from fastapi.testclient import TestClient

from src.models.patient import Patient


def _create_sample_patient(client: TestClient) -> Patient:
    form = {
        "title": "Mr",
        "first_name": "Albert",
        "last_name": "Doe",
        "sex": "male",
        "dob": "1990-01-01",
        "email": "albert.doe@example.com",
        "phone": "1234567890",
    }

    resp = client.post("/patients", data=form, follow_redirects=False)
    patient_url = resp.headers.get("location")
    assert patient_url.startswith("/patients/")

    # Extract patient ID from the redirect URL
    patient_id = int(patient_url.rstrip('/').split('/')[-1])
    return Patient(patient_id=patient_id, **form)


def test_patient_details_page_renders(client: TestClient):
    patient = _create_sample_patient(client)

    resp = client.get(f"/patients/{patient.patient_id}")
    assert resp.status_code == 200
    html = resp.text

    # Page level checks
    assert "Patient Details" in html
    assert "Patient Summary" in html
    assert "Medical checks" in html

    # Patient data should be title-cased/formatted by the model behavior
    assert "Albert" in html
    assert "Doe" in html
    assert "male" in html
    # Email isn't displayed on the details summary tile currently

    # UI containers used by the details page
    assert "checksTiles" in html  # container for the tiles grid

    patient.first_name = "jonathan"
    patient.last_name = "wick"

    resp = client.put(f"/patients/{patient.patient_id}", data=patient.model_dump())
    assert resp.status_code == 200
    html = resp.text

    assert "Jonathan" in html
    assert "Wick" in html


def test_patient_details_not_found(client: TestClient):
    resp = client.get("/patients/999")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
