from datetime import datetime
from pathlib import Path

from fastapi.testclient import TestClient


def test_patients_page_initially_empty(client: TestClient):
    resp = client.get("/patients")
    assert resp.status_code == 200
    html = resp.text
    assert "Patients" in html
    assert "Add New Patient" in html
    assert "Search patients" in html


def test_create_patient_and_list(client: TestClient):
    form = {
        "title": "Mr",
        "first_name": "john",
        "last_name": "doe",
        "sex": "male",
        "dob": "1990-01-01",
        "email": "test@example.com",
        "phone": "1234567890",
    }

    resp = client.post("/patients", data=form)
    html = resp.text

    assert "John" in html
    assert "Doe" in html

    assert str(datetime.now().year - 1990) in html # age

    resp = client.get("/patients")

    assert resp.status_code == 200
    html = resp.text
    assert "John" in html
    assert "Doe" in html
    assert "male" in html
