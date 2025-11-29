import re

from fastapi.testclient import TestClient

from src.models.patient import Patient


def _create_sample_patient(client: TestClient) -> Patient:
    form = {
        "title": "Mr",
        "first_name": "john",
        "middle_name": "albert",
        "last_name": "doe",
        "sex": "male",
        "dob": "1990-01-02",
        "email": "JOHN.DOE@EXAMPLE.COM",
        "phone": "+1-555-0100",
    }
    # Create patient; follow redirect to patients list to be able to extract the details link
    resp = client.post("/patients", data=form, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.text

    m = re.search(r"/patients/(\d+)", html)
    assert m, "Expected patients list to contain a details link"
    return Patient(patient_id=int(m.group(1)), **form)


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
    assert "John" in html
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
