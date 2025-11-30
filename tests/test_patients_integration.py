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


def test_update_patient(client: TestClient):
    # First, create a patient
    create_form = {
        "title": "Mr",
        "first_name": "john",
        "last_name": "doe",
        "sex": "male",
        "dob": "1990-01-01",
        "email": "john.doe@example.com",
        "phone": "1234567890",
    }
    
    resp = client.post("/patients", data=create_form)

    patient_id = resp.url.path.split('/')[-1]
    
    # Now update the patient
    update_form = {
        "_method": "PUT",  # Simulate form submission with method override
        "title": "Dr",
        "first_name": "johnathan",
        "last_name": "doe",
        "sex": "male",
        "dob": "1985-01-01",
        "email": "dr.john.doe@example.com",
        "phone": "0987654321",
    }
    
    resp = client.post(f"/patients/{patient_id}", data=update_form, follow_redirects=True)
    
    assert resp.status_code == 200
    html = resp.text
    
    assert "Johnathan" in html
    assert "Doe" in html
    assert str(datetime.now().year - 1985) in html

    resp = client.get("/patients")
    html = resp.text

    assert resp.status_code == 200
    assert "Johnathan" in html
    assert "Doe" in html
    assert "dr.john.doe@example.com" in html
    assert "0987654321" in html
