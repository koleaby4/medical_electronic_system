from datetime import date

from fastapi.testclient import TestClient


def _create_physicals_check(
    client: TestClient,
    patient_id: int,
    *,
    status: str = "Red",
    notes: str | None = None,
    with_item: bool = False,
) -> int:
    today = date.today().isoformat()
    form: dict[str, str] = {
        "type": "physicals",
        "date": today,
        "status": status,
    }

    if with_item:
        form.update(
            {
                "param_name_0": "weight",
                "param_value_0": "72.0",
                "param_units_0": "kg",
            }
        )
    else:
        form["param_count"] = "0"

    if notes:
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


def test_update_status_invalid_value_returns_400(client: TestClient, create_patient):
    patient_id = create_patient()
    check_id = _create_physicals_check(client, patient_id, status="Amber")

    resp = client.post(
        f"/patients/{patient_id}/medical_checks/{check_id}/status",
        data={"status": "Blue"},
        follow_redirects=False,
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body.get("detail") == "Invalid status value"


def test_list_medical_checks_excludes_patient_id_in_json(client: TestClient, create_patient):
    patient_id = create_patient()
    _ = _create_physicals_check(client, patient_id, status="Green", with_item=True)

    resp = client.get(f"/patients/{patient_id}/medical_checks")
    assert resp.status_code == 200
    data = resp.json()
    assert "records" in data
    rec = data["records"][0]
    assert "patient_id" not in rec  # excluded by model
    # but other fields are present
    assert rec.get("check_id") is not None
    assert rec.get("status") in {"Red", "Amber", "Green"}


def test_timeseries_unknown_item_returns_empty_records(client: TestClient, create_patient):
    patient_id = create_patient()
    _ = _create_physicals_check(client, patient_id, status="Green", with_item=True)

    resp = client.get(
        f"/patients/{patient_id}/medical_checks/timeseries",
        params={"check_template": "physicals", "item_name": "height"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("records") == []


def test_create_medical_check_without_param_count_auto_detects_items(client: TestClient, create_patient):
    patient_id = create_patient()
    _ = _create_physicals_check(client, patient_id, status="Red", with_item=True)

    resp = client.get(f"/patients/{patient_id}/medical_checks")
    assert resp.status_code == 200
    data = resp.json()
    rec = data["records"][0]
    items = rec.get("medical_check_items")
    assert isinstance(items, list) and len(items) == 1
    item = items[0]
    assert item.get("name") == "weight"
    assert item.get("units") == "kg"
    assert item.get("value") == "72.0"
