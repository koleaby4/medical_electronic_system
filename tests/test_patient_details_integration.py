import re

from fastapi.testclient import TestClient


def _create_sample_patient(client: TestClient) -> int:
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

    # Find the first details link: /patients/{id}/details
    m = re.search(r"/patients/(\d+)/details", html)
    assert m, "Expected patients list to contain a details link"
    return int(m.group(1))


def test_patient_details_page_renders(client: TestClient):
    patient_id = _create_sample_patient(client)

    resp = client.get(f"/patients/{patient_id}/details")
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


def test_patient_details_not_found(client: TestClient):
    resp = client.get("/patients/999/details")
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data
    assert "patient_id=999" in data["detail"]
