from fastapi.testclient import TestClient


def test_physicals_new_page_renders(client: TestClient, create_patient):
    patient_id = create_patient()

    # Create a medical check type named "physicals" with a sample item "height"
    resp_admin = client.post(
        "/admin/medical_check_templates",
        json={
            "name": "physicals",
            "items": [
                {"name": "height", "units": "cm", "input_type": "number", "placeholder": "e.g. 180"},
            ],
        },
    )
    assert resp_admin.status_code == 201
    template_id = resp_admin.json()["template_id"]

    # Use the generic new page with template_id
    resp = client.get(
        f"/patients/{patient_id}/medical_checks/new?check_template_id={template_id}", follow_redirects=True
    )
    html = resp.text

    assert "Add physicals check" in html
    assert "Name" in html
    assert "Units" in html
    assert "Value" in html

    assert "height" in html


def test_post_physicals_with_notes_persisted_in_api(client: TestClient, create_patient):
    patient_id = create_patient()

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
