from fastapi.testclient import TestClient


def test_patient_not_found_errors(client: TestClient):
    # Edit form 404
    resp = client.get("/patients/9999/edit")
    assert resp.status_code == 404

    # Update 404 - must use _method=PUT to reach the logic that returns 404
    resp = client.post("/patients/9999", data={"_method": "PUT", "first_name": "Ghost"})
    assert resp.status_code == 404

    # Details 404
    resp = client.get("/patients/9999")
    assert resp.status_code == 404


def test_update_patient_success(client: TestClient, create_patient):
    patient_id = create_patient()

    # Update patient info
    update_data = {
        "_method": "PUT",
        "title": "Dr",
        "first_name": "Jane",
        "last_name": "Smith",
        "sex": "female",
        "dob": "1985-05-05",
        "email": "jane.smith@example.com",
        "phone": "987654321",
        "line_1": "Updated St",
        "town": "New Town",
        "postcode": "N1 1AA",
        "country": "UK",
    }
    # TestClient follow_redirects=True should return 200
    resp = client.post(f"/patients/{patient_id}", data=update_data, follow_redirects=True)
    assert resp.status_code == 200
    content = resp.text
    assert "Jane" in content
    assert "Smith" in content


def test_update_patient_method_override(client: TestClient, create_patient):
    patient_id = create_patient()
    # Provide all required fields for Patient model
    update_data = {
        "_method": "PUT",
        "title": "Mr",
        "first_name": "Overridden",
        "last_name": "Doe",
        "sex": "male",
        "dob": "1990-01-01",
        "email": "test@example.com",
        "phone": "123",
        "line_1": "St",
        "town": "Town",
        "postcode": "PC",
        "country": "UK",
    }
    resp = client.post(f"/patients/{patient_id}", data=update_data, follow_redirects=False)
    assert resp.status_code in (303, 307)

    resp = client.get(f"/patients/{patient_id}")
    assert "Overridden" in resp.text


def test_update_patient_json_success(client: TestClient, create_patient):
    patient_id = create_patient()
    update_data = {
        "title": "Dr",
        "first_name": "Jane",
        "last_name": "Smith",
        "sex": "female",
        "dob": "1985-05-05",
        "email": "jane.smith@example.com",
        "phone": "987654321",
        "line_1": "Updated St",
        "town": "New Town",
        "postcode": "N1 1AA",
        "country": "UK",
    }
    resp = client.put(f"/patients/{patient_id}", json=update_data)
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Jane"


def test_list_patients_html(client: TestClient, create_patient):
    create_patient()
    resp = client.get("/patients")
    assert resp.status_code == 200
    assert "Patients" in resp.text
