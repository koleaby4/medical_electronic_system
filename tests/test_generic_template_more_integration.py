from datetime import date

from fastapi.testclient import TestClient


def _create_template(client: TestClient, name: str, items: list[dict]) -> int:
    """Create a template via JSON API."""
    resp = client.post(
        "/admin/medical_check_templates",
        json={
            "name": name,
            "items": items,
        },
    )
    assert resp.status_code == 201
    return resp.json()["template_id"]


def test_generic_new_requires_template_id(client: TestClient, create_patient):
    patient_id = create_patient()

    # Create two templates
    tid_z = _create_template(
        client,
        name="Z Second",
        items=[{"name": "weight", "units": "kg", "input_type": "number", "placeholder": "e.g. 75.5"}],
    )
    tid_a = _create_template(
        client,
        name="A First",
        items=[{"name": "systolic", "units": "mmHg", "input_type": "number", "placeholder": "e.g. 120"}],
    )

    # Request with tid_a
    resp = client.get(f"/patients/{patient_id}/medical_checks/new?check_template_id={tid_a}")
    assert resp.status_code == 200
    assert "Add A First check" in resp.text

    # Request with tid_z
    resp = client.get(f"/patients/{patient_id}/medical_checks/new?check_template_id={tid_z}")
    assert resp.status_code == 200
    assert "Add Z Second check" in resp.text

    # Request without template_id should fail with 422
    resp = client.get(f"/patients/{patient_id}/medical_checks/new")
    assert resp.status_code == 422


def test_generic_new_renders_text_input_and_placeholder(client: TestClient, create_patient):
    patient_id = create_patient()
    template_id = _create_template(
        client,
        name="Notes",
        items=[{"name": "note", "units": "", "input_type": "short_text", "placeholder": "enter note"}],
    )

    resp = client.get(f"/patients/{patient_id}/medical_checks/new?check_template_id={template_id}")
    assert resp.status_code == 200
    html = resp.text

    # Input type should be text, and placeholder should be present
    assert 'name="param_value_0"' in html
    assert 'type="text"' in html
    assert 'placeholder="enter note"' in html


def test_generic_post_with_multiple_items_persists_all_values(client: TestClient, create_patient):
    patient_id = create_patient()
    _create_template(
        client,
        name="Vitals2",
        items=[
            {"name": "weight", "units": "kg", "input_type": "number", "placeholder": "e.g. 75.5"},
            {"name": "height", "units": "cm", "input_type": "number", "placeholder": "e.g. 180"},
        ],
    )

    today = date.today().isoformat()
    form = {
        "type": "Vitals2",
        "date": today,
        "status": "Green",
        "param_count": 2,
        "param_name_0": "weight",
        "param_units_0": "kg",
        "param_value_0": "75.5",
        "param_name_1": "height",
        "param_units_1": "cm",
        "param_value_1": "180",
    }

    resp_post = client.post(f"/patients/{patient_id}/medical_checks", data=form, follow_redirects=False)
    assert resp_post.status_code in (303, 307)

    resp_get = client.get(f"/patients/{patient_id}/medical_checks")
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert data.get("records")
    rec = data["records"][0]
    items = rec.get("medical_check_items") or []

    assert any(i.get("name") == "weight" and i.get("value") == "75.5" and i.get("units") == "kg" for i in items)
    assert any(i.get("name") == "height" and i.get("value") == "180" and i.get("units") == "cm" for i in items)
