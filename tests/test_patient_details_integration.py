from fastapi.testclient import TestClient


def _patient_overrides():
    return {
        "title": "Mr",
        "first_name": "Albert",
        "last_name": "Doe",
        "sex": "male",
        "dob": "1990-01-01",
        "email": "albert.doe@example.com",
        "phone": "1234567890",
    }


def test_patient_details_page_renders(client: TestClient, create_patient):
    patient_id = create_patient(_patient_overrides())

    resp = client.get(f"/patients/{patient_id}")
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

    update_form = {
        "title": "Mr",
        "first_name": "jonathan",
        "last_name": "wick",
        "sex": "male",
        "dob": "1990-01-01",
        "email": "albert.doe@example.com",
        "phone": "1234567890",
    }

    resp = client.put(f"/patients/{patient_id}", data=update_form)
    assert resp.status_code == 200
    html = resp.text

    assert "Jonathan" in html
    assert "Wick" in html


def test_patient_details_not_found(client: TestClient):
    resp = client.get("/patients/999")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
