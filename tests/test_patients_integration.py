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
        "middle_name": "albert",
        "last_name": "doe",
        "sex": "male",
        "dob": "1990-01-02",
        "email": "JOHN.DOE@EXAMPLE.COM",
        "phone": "+1-555-0100",
    }

    resp = client.post("/patients", data=form, follow_redirects=True)

    assert resp.status_code == 200
    html = resp.text

    assert "Mr" in html
    assert "John" in html
    assert "Albert" in html
    assert "Doe" in html
    assert "male" in html
    assert "john.doe@example.com" in html
