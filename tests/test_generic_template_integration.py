from datetime import date

from fastapi.testclient import TestClient


def _create_template(client: TestClient, name: str = "Vitals") -> int:
    """Create a simple template via admin endpoint with one numeric item 'weight'."""
    resp = client.post(
        "/admin/medical_check_templates",
        json={
            "name": name,
            "items": [
                {"name": "weight", "units": "kg", "input_type": "number", "placeholder": "75.5"},
            ],
        },
    )
    assert resp.status_code == 201
    return resp.json()["template_id"]


def test_generic_new_page_renders_with_numeric_step_0_1(client: TestClient, create_patient):
    patient_id = create_patient()
    template_id = _create_template(client, name="Vitals")

    resp = client.get(f"/patients/{patient_id}/medical_checks/new?check_template_id={template_id}")
    assert resp.status_code == 200
    html = resp.text

    # Header reflects template name chosen (first by name)
    assert "Add Vitals check" in html

    # Numeric inputs rendered from template should allow 1-decimal values (step="0.1")
    # and use type="number"
    assert 'id="param_0"' in html
    assert 'type="number"' in html
    assert 'step="0.1"' in html


def test_generic_post_accepts_decimal_and_persists(client: TestClient, create_patient):
    patient_id = create_patient()
    _create_template(client, name="Vitals")

    today = date.today().isoformat()
    form = {
        "type": "Vitals",
        "date": today,
        "status": "Green",
        "param_count": 1,
        "param_name_0": "weight",
        "param_units_0": "kg",
        "param_value_0": "75.5",
    }

    resp_post = client.post(f"/patients/{patient_id}/medical_checks", data=form, follow_redirects=False)
    assert resp_post.status_code in (303, 307)

    # Read back via API and verify item value is persisted as provided
    resp_get = client.get(f"/patients/{patient_id}/medical_checks")
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert data.get("records")
    rec = data["records"][0]
    items = rec.get("medical_check_items") or []
    # There should be one item with decimal value preserved as string
    assert any(i.get("name") == "weight" and i.get("value") == "75.5" and i.get("units") == "kg" for i in items)


def test_generic_new_page_patient_not_found_returns_404(client: TestClient):
    resp = client.get("/patients/999999/medical_checks/new?check_template_id=1")
    assert resp.status_code == 404
    body = resp.json()
    assert "detail" in body
    assert "patient_id=999999" in body["detail"]
