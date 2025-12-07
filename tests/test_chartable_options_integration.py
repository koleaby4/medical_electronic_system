from datetime import date

from fastapi.testclient import TestClient


def _create_template_with_numeric(client: TestClient, name: str = "Vitals") -> None:
    form = {
        "template_name": name,
        "items[0][name]": "weight",
        "items[0][units]": "kg",
        "items[0][input_type]": "number",
        "items[0][placeholder]": "e.g. 75.5",
    }
    resp = client.post("/admin/medical_check_templates/new", data=form, follow_redirects=False)
    assert resp.status_code in (303, 307)


def _create_check_with_item(client: TestClient, patient_id: int, check_type: str = "Vitals") -> None:
    form = {
        "type": check_type,
        "date": date.today().isoformat(),
        "status": "Green",
        "param_count": 1,
        "param_name_0": "weight",
        "param_units_0": "kg",
        "param_value_0": "73.2",
    }
    resp = client.post(f"/patients/{patient_id}/medical_checks", data=form, follow_redirects=False)
    assert resp.status_code in (303, 307)


def test_chartable_options_happy_path(client: TestClient, create_patient):
    patient_id = create_patient()
    _create_template_with_numeric(client)
    _create_check_with_item(client, patient_id)

    resp = client.get(f"/patients/{patient_id}/medical_checks/chartable_options")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data.get("records"), list)
    labels = [r.get("label") for r in data["records"]]
    # Should contain our Vitals -> weight option
    assert any(l and "Vitals -> weight" in l for l in labels)


def test_chartable_options_empty_when_no_items(client: TestClient, create_patient):
    patient_id = create_patient()
    _create_template_with_numeric(client)
    # No checks created yet
    resp = client.get(f"/patients/{patient_id}/medical_checks/chartable_options")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("records") == []


def test_chartable_options_patient_not_found(client: TestClient):
    resp = client.get("/patients/99999/medical_checks/chartable_options")
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body
    assert "patient_id=99999" in body["detail"]
