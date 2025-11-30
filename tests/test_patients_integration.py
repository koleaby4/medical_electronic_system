from fastapi.testclient import TestClient


def test_patients_page_initially_empty(client: TestClient):
    resp = client.get("/patients")
    assert resp.status_code == 200
    html = resp.text
    assert "Patients" in html
    assert "Add New Patient" in html
    assert "Search patients" in html


def test_create_patient_and_list(client: TestClient, create_patient):
    create_patient(
        {
            "first_name": "john",
            "last_name": "doe",
            "sex": "male",
            "dob": "1990-01-01",
            "email": "test@example.com",
            "phone": "1234567890",
        }
    )

    resp = client.get("/patients")

    assert resp.status_code == 200
    html = resp.text
    assert "John" in html
    assert "Doe" in html
    assert "male" in html


def test_update_patient(client: TestClient, create_patient):
    # First, create a patient
    patient_id = create_patient(
        {
            "first_name": "john",
            "last_name": "doe",
            "sex": "male",
            "dob": "1990-01-01",
            "email": "john.doe@example.com",
            "phone": "1234567890",
        }
    )

    # Now update the patient via PUT
    update_form = {
        "title": "Dr",
        "first_name": "johnathan",
        "last_name": "doe",
        "sex": "male",
        "dob": "1985-01-01",
        "email": "dr.john.doe@example.com",
        "phone": "0987654321",
    }

    resp = client.put(f"/patients/{patient_id}", data=update_form)

    assert resp.status_code == 200
    html = resp.text

    assert "Johnathan" in html
    assert "Doe" in html

    resp = client.get("/patients")
    html = resp.text

    assert resp.status_code == 200
    assert "Johnathan" in html
    assert "Doe" in html
    assert "dr.john.doe@example.com" in html
    assert "0987654321" in html
