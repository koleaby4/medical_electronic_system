import io
from datetime import date

from fastapi.testclient import TestClient


def test_upload_and_view_attachment(client: TestClient):
    # 1. Create a sample patient
    patient_form = {
        "title": "Mr",
        "first_name": "Attach",
        "last_name": "Test",
        "sex": "male",
        "dob": "1990-01-01",
        "email": "attach@example.com",
        "phone": "555-1234",
    }
    client.post("/patients", data=patient_form, follow_redirects=True)

    # Get patient ID
    resp = client.get("/patients")
    # Assuming the last created patient is at the top or we can find by name
    # But let's just get the first one from the list as it's a fresh test DB usually
    # or better, use the API if available.
    patients_resp = client.get("/patients", headers={"Accept": "application/json"})
    patients = patients_resp.json()["records"]
    patient_id = patients[0]["patient_id"]

    # 2. Create a medical check with an attachment
    today = date.today().isoformat()
    check_form = {
        "type": "blood",
        "date": today,
        "status": "Green",
        "notes": "Testing attachments",
        "param_count": "0",
    }

    file_content = b"fake file content"
    files = [("attachments", ("test.txt", io.BytesIO(file_content), "text/plain"))]

    resp = client.post(f"/patients/{patient_id}/medical_checks", data=check_form, files=files, follow_redirects=True)
    assert resp.status_code == 200

    # 3. Verify the check has the attachment via API
    checks_resp = client.get(f"/patients/{patient_id}/medical_checks", headers={"Accept": "application/json"})
    checks = checks_resp.json()["records"]
    check = checks[0]
    check_id = check["check_id"]
    assert len(check["attachments"]) == 1
    attachment = check["attachments"][0]
    assert attachment["filename"] == "test.txt"

    # 4. Verify the attachment is viewable (GET the file)
    # The path should be /patients/{id}/medical_checks/attachments/{patient_id}/{iso-date}/{filename}
    attachment_path = attachment["file_path"]  # e.g. "1/2026-03-07/test.txt"
    view_url = f"/patients/{patient_id}/medical_checks/attachments/{attachment_path}"

    resp = client.get(view_url)
    assert resp.status_code == 200
    assert resp.content == file_content

    # 5. Check the details page contains the link
    resp = client.get(f"/patients/{patient_id}/medical_checks/{check_id}")
    assert resp.status_code == 200
    assert "test.txt" in resp.text
    assert view_url in resp.text

    # Cleanup: remove created file and directory
    # (In a real test we'd probably use a temporary directory for attachments)
    # For now let's just leave it as it's a test environment.
