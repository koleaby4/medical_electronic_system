import re
from datetime import date

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
    resp = client.post("/patients", data=form, follow_redirects=True)
    assert resp.status_code == 200
    m = re.search(r"/patients/(\d+)/details", resp.text)
    assert m
    return int(m.group(1))


def _create_physicals_check(client: TestClient, patient_id: int, status: str = "Red", notes: str | None = None) -> int:
    today = date.today().isoformat()
    form = {
        "type": "physicals",
        "date": today,
        "status": status,
        "param_count": 0,
    }
    if notes is not None:
        form["notes"] = notes

    resp_post = client.post(f"/patients/{patient_id}/medical_checks", data=form, follow_redirects=False)
    assert resp_post.status_code in (303, 307)

    # Read back via API to obtain check_id
    resp_get = client.get(f"/patients/{patient_id}/medical_checks")
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert data.get("records")
    check_id = data["records"][0]["check_id"]
    assert check_id is not None
    return int(check_id)


def test_medical_check_details_page_and_status_update_flow(client: TestClient):
    patient_id = _create_sample_patient(client)
    check_id = _create_physicals_check(client, patient_id, status="Amber", notes="initial")

    # GET details page
    resp = client.get(f"/patients/{patient_id}/medical_checks/{check_id}")
    assert resp.status_code == 200
    html = resp.text
    assert "Medical Check Details" in html
    # Page shows current status pre-selected
    assert '<option value="Amber" selected' in html

    # Change status to Green
    resp_upd = client.post(
        f"/patients/{patient_id}/medical_checks/{check_id}/status",
        data={"status": "Green"},
        follow_redirects=False,
    )
    assert resp_upd.status_code in (303, 307)

    # Verify via API the status changed
    resp_get = client.get(f"/patients/{patient_id}/medical_checks")
    assert resp_get.status_code == 200
    data = resp_get.json()
    rec = next((r for r in data.get("records", []) if r.get("check_id") == check_id), None)
    assert rec is not None
    assert rec.get("status") == "Green"
