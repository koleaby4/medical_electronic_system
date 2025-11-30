from fastapi.testclient import TestClient
import re


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
    resp = client.post("/patients", data=form, follow_redirects=True)
    assert resp.status_code == 200

    m = re.search(r"/patients/(\d+)", str(resp.url))
    assert m
    return int(m.group(1))


def test_physicals_new_page_renders(client: TestClient):
    patient_id = _create_sample_patient(client)

    resp = client.get(f"/patients/{patient_id}/medical_checks/physicals/new", follow_redirects=True)
    html = resp.text

    assert "Add physicals check" in html
    assert "Name" in html
    assert "Units" in html
    assert "Value" in html

    assert "height" in html


def test_post_physicals_with_notes_persisted_in_api(client: TestClient):
    patient_id = _create_sample_patient(client)

    from datetime import date

    today = date.today().isoformat()
    notes_text = "Patient reported mild headache."

    form = {
        "type": "physicals",
        "date": today,
        "status": "Red",
        "notes": notes_text,
        "param_count": 0,
    }

    resp_post = client.post(f"/patients/{patient_id}/medical_checks", data=form, follow_redirects=False)
    assert resp_post.status_code in (303, 307)

    resp_get = client.get(f"/patients/{patient_id}/medical_checks")
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert "records" in data
    assert len(data["records"]) >= 1
    record = data["records"][0]
    assert record.get("notes") == notes_text
