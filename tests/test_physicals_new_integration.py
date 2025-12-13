from fastapi.testclient import TestClient


def test_physicals_new_page_renders(client: TestClient, create_patient):
    patient_id = create_patient()

    # Create a medical check type named "physicals" with a sample item "height"
    form = {
        "template_name": "physicals",
        "items[0][name]": "height",
        "items[0][units]": "cm",
        "items[0][input_type]": "number",
        "items[0][placeholder]": "e.g. 180",
    }
    resp_admin = client.post("/admin/medical_check_types/new", data=form, follow_redirects=False)
    assert resp_admin.status_code in (303, 307)

    # Use the generic new page (it will select the first available type, which is the one we created)
    resp = client.get(f"/patients/{patient_id}/medical_checks/new", follow_redirects=True)
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
