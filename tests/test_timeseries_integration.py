from datetime import date, timedelta
import re

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


def _create_physicals_with_item(
    client: TestClient, patient_id: int, check_date: date, status: str, item_name: str, value: str, units: str
) -> None:
    form = {
        "type": "physicals",
        "date": check_date.isoformat(),
        "status": status,
        "param_count": 1,
        "param_name_0": item_name,
        "param_value_0": value,
        "param_units_0": units,
    }
    resp = client.post(f"/patients/{patient_id}/medical_checks", data=form, follow_redirects=False)
    assert resp.status_code in (303, 307)


def test_timeseries_happy_path_returns_sorted_values(client: TestClient):
    patient_id = _create_sample_patient(client)

    d1 = date.today() - timedelta(days=10)
    d2 = date.today() - timedelta(days=5)

    _create_physicals_with_item(client, patient_id, d2, "Green", "weight", "71", "kg")
    _create_physicals_with_item(client, patient_id, d1, "Green", "weight", "70.5", "kg")

    resp = client.get(
        f"/patients/{patient_id}/medical_checks/timeseries",
        params={"check_type": "physicals", "item_name": "weight"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "records" in data
    records = data["records"]
    assert isinstance(records, list)

    # Should be sorted by date ascending
    assert [r["date"] for r in records] == sorted(r["date"] for r in records)

    # Values are strings (as stored) and units preserved
    assert {r["units"] for r in records} == {"kg"}

    # Check the exact values sequence given dates
    # Map by date for determinism
    by_date = {r["date"]: r for r in records}
    assert by_date[d1.isoformat()]["value"] == "70.5"
    assert by_date[d2.isoformat()]["value"] == "71"


def test_timeseries_patient_not_found_returns_404(client: TestClient):
    resp = client.get(
        "/patients/9999/medical_checks/timeseries",
        params={"check_type": "physicals", "item_name": "weight"},
    )
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body
    assert "patient_id=9999" in body["detail"]
