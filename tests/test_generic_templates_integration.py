from datetime import date

from fastapi.testclient import TestClient


def _create_template(client: TestClient, name: str, items: list[dict] | None = None) -> int:
    """Create a template via JSON API."""
    if items is None:
        items = [{"name": "weight", "units": "kg", "input_type": "number", "placeholder": "75.5"}]
    resp = client.post(
        "/admin/medical_check_templates",
        json={
            "name": name,
            "items": items,
        },
    )
    assert resp.status_code == 201
    return resp.json()["template_id"]


def test_generic_template_new_page_rendering(client: TestClient, create_patient):
    patient_id = create_patient()

    # Test numeric input rendering
    tid_vitals = _create_template(client, name="Vitals")
    resp = client.get(f"/patients/{patient_id}/medical_checks/new?check_template_id={tid_vitals}")
    assert resp.status_code == 200
    html = resp.text
    assert "Add Vitals check" in html
    assert 'type="number"' in html
    assert 'step="0.1"' in html

    # Test text input rendering and placeholder
    tid_notes = _create_template(
        client,
        name="Notes",
        items=[{"name": "note", "units": "", "input_type": "short_text", "placeholder": "enter note"}],
    )
    resp = client.get(f"/patients/{patient_id}/medical_checks/new?check_template_id={tid_notes}")
    assert resp.status_code == 200
    html = resp.text
    assert 'type="text"' in html
    assert 'placeholder="enter note"' in html


def test_generic_template_new_template_selection(client: TestClient, create_patient):
    patient_id = create_patient()
    tid_z = _create_template(client, name="Z Second")
    tid_a = _create_template(client, name="A First")

    resp = client.get(f"/patients/{patient_id}/medical_checks/new?check_template_id={tid_a}")
    assert "Add A First check" in resp.text

    resp = client.get(f"/patients/{patient_id}/medical_checks/new?check_template_id={tid_z}")
    assert "Add Z Second check" in resp.text

    # Without template_id
    resp = client.get(f"/patients/{patient_id}/medical_checks/new")
    assert resp.status_code == 422


def test_generic_template_post_and_persistence(client: TestClient, create_patient):
    patient_id = create_patient()
    _create_template(
        client,
        name="FullVitals",
        items=[
            {"name": "weight", "units": "kg", "input_type": "number", "placeholder": "e.g. 75.5"},
            {"name": "height", "units": "cm", "input_type": "number", "placeholder": "e.g. 180"},
        ],
    )

    today = date.today().isoformat()
    form = {
        "type": "FullVitals",
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
    items = resp_get.json()["records"][0]["medical_check_items"]

    assert any(i["name"] == "weight" and i["value"] == "75.5" for i in items)
    assert any(i["name"] == "height" and i["value"] == "180" for i in items)


def test_generic_template_new_patient_not_found(client: TestClient):
    resp = client.get("/patients/999999/medical_checks/new?check_template_id=1")
    assert resp.status_code == 404
