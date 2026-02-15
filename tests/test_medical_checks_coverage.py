from fastapi.testclient import TestClient


def test_medical_check_404_not_found(client: TestClient, create_patient):
    patient_id = create_patient()

    # 404 for patient not found
    resp = client.get("/patients/9999/medical_checks/1")
    assert resp.status_code == 404
    assert "Patient with patient_id=9999 not found" in resp.json()["detail"]

    # 404 for check not found
    resp = client.get(f"/patients/{patient_id}/medical_checks/9999")
    assert resp.status_code == 404
    assert "Medical check with check_id=9999 not found" in resp.json()["detail"]


def test_update_medical_check_json(client: TestClient, create_patient):
    patient_id = create_patient()

    # Create a check first
    form: dict[str, str | int] = {
        "type": "physicals",
        "date": "2025-01-01",
        "status": "Green",
        "notes": "Old notes",
        "param_count": 0,
    }
    client.post(f"/patients/{patient_id}/medical_checks", data={k: str(v) for k, v in form.items()})

    resp_list = client.get(f"/patients/{patient_id}/medical_checks")
    check_id = resp_list.json()["records"][0]["check_id"]

    # Update status and notes via PUT JSON
    update_data = {"status": "Red", "notes": "New updated notes"}
    resp = client.put(f"/patients/{patient_id}/medical_checks/{check_id}", json=update_data)
    assert resp.status_code == 200
    updated = resp.json()
    assert updated["status"] == "Red"
    assert updated["notes"] == "New updated notes"

    # Test invalid status via JSON
    resp = client.put(f"/patients/{patient_id}/medical_checks/{check_id}", json={"status": "InvalidStatus"})
    assert resp.status_code == 422

    # Test 404 for patient/check in PUT
    resp = client.put(f"/patients/9999/medical_checks/{check_id}", json={"notes": "test"})
    assert resp.status_code == 404

    resp = client.put(f"/patients/{patient_id}/medical_checks/9999", json={"notes": "test"})
    assert resp.status_code == 404


def test_delete_medical_check(client: TestClient, create_patient):
    patient_id = create_patient()

    # Create a check
    form: dict[str, str | int] = {"type": "physicals", "date": "2025-01-01", "status": "Green", "param_count": 0}
    client.post(f"/patients/{patient_id}/medical_checks", data={k: str(v) for k, v in form.items()})
    resp_list = client.get(f"/patients/{patient_id}/medical_checks")
    check_id = resp_list.json()["records"][0]["check_id"]

    # Delete it
    resp = client.delete(f"/patients/{patient_id}/medical_checks/{check_id}")
    assert resp.status_code == 204

    # Verify it's gone
    resp_list = client.get(f"/patients/{patient_id}/medical_checks")
    assert len(resp_list.json()["records"]) == 0

    # Delete non-existent check (should return 204 as per code)
    resp = client.delete(f"/patients/{patient_id}/medical_checks/9999")
    assert resp.status_code == 204


def test_timeseries_patient_not_found(client: TestClient):
    resp = client.get("/patients/9999/medical_checks/timeseries", params={"check_template": "a", "item_name": "b"})
    assert resp.status_code == 404


def test_chartable_options_patient_not_found(client: TestClient):
    resp = client.get("/patients/9999/medical_checks/chartable_options")
    assert resp.status_code == 404


def test_create_medical_check_missing_fields(client: TestClient, create_patient):
    patient_id = create_patient()
    # Missing 'type', 'date', 'status' which are Form(...) in routes/medical_checks.py:54
    resp = client.post(f"/patients/{patient_id}/medical_checks", data={})
    assert resp.status_code == 422


def test_new_medical_check_page_404(client: TestClient):
    # template_id=1 exists? Migrated DB should have none or some.
    # Let's try a high ID
    resp = client.get("/patients/1/medical_checks/new/9999")
    assert resp.status_code == 404
