from fastapi.testclient import TestClient


def _create_template_json(client: TestClient, name: str, items: list[dict]) -> int:
    resp = client.post(
        "/admin/medical_check_templates",
        json={
            "name": name,
            "items": items,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    template_id = body.get("template_id")
    assert isinstance(template_id, int) and template_id > 0
    return template_id


def test_edit_page_prefilled_and_update_via_html_form(client: TestClient):
    # Arrange: create a template with two items via JSON API
    template_id = _create_template_json(
        client,
        name="Vitals",
        items=[
            {"name": "weight", "units": "kg", "input_type": "number", "placeholder": "75.5"},
            {"name": "note", "units": "", "input_type": "short_text", "placeholder": "optional"},
        ],
    )

    # Act: open edit page (HTML)
    resp_edit = client.get(f"/admin/medical_check_templates/{template_id}/edit")
    assert resp_edit.status_code == 200
    html = resp_edit.text

    # Assert: form is prefilled
    assert "Edit Medical Check Template" in html
    assert "Vitals" in html
    assert 'name="check_name"' in html
    assert "Cancel" in html
    # Items rendered as rows with correct values
    assert "weight" in html
    assert "note" in html
    assert "kg" in html
    assert "75.5" in html
    assert "short_text" in html

    # Act: submit HTML form to update name (should succeed now)
    form = {
        "template_id": str(template_id),
        "check_name": "Vitals Updated",
        "items[0][name]": "weight",
        "items[0][units]": "kg",
        "items[0][input_type]": "number",
        "items[0][placeholder]": "80.0",  # Attempting to change placeholder
    }
    resp_post = client.post("/admin/medical_check_templates/new", data=form, follow_redirects=False)
    assert resp_post.status_code == 303

    # Assert: JSON GET reflects name update but NOT items update
    resp_get = client.get(f"/admin/medical_check_templates/{template_id}")
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert data["name"] == "Vitals Updated"
    # Placeholder should STILL be 75.5
    assert data["items"][0]["placeholder"] == "75.5"

    # Assert: listing page shows updated comma-separated fields
    resp_list = client.get("/admin/medical_check_templates")
    assert resp_list.status_code == 200
    list_html = resp_list.text
    # Name and items visible in the table
    assert "Vitals Updated" in list_html
    assert "weight" in list_html
    assert "note" in list_html


def test_edit_replacing_with_more_items_and_order_preserved(client: TestClient):
    # Arrange: create a template with one item
    template_id = _create_template_json(
        client,
        name="Exam",
        items=[
            {"name": "height", "units": "cm", "input_type": "number", "placeholder": "180"},
        ],
    )

    # Update via HTML form to have two items (should succeed for name but items remain same)
    form = {
        "template_id": str(template_id),
        "check_name": "Exam Updated",
        "items[0][name]": "systolic",
        "items[0][units]": "mmHg",
        "items[0][input_type]": "number",
        "items[0][placeholder]": "120",
        "items[1][name]": "diastolic",
        "items[1][units]": "mmHg",
        "items[1][input_type]": "number",
        "items[1][placeholder]": "80",
    }
    resp_post = client.post("/admin/medical_check_templates/new", data=form, follow_redirects=False)
    assert resp_post.status_code == 303

    # Read back via JSON and verify items have NOT changed, but name DID
    resp_get = client.get(f"/admin/medical_check_templates/{template_id}")
    assert resp_get.status_code == 200
    data = resp_get.json()
    assert data["name"] == "Exam Updated"
    items = data.get("items") or []
    assert [i["name"] for i in items] == ["height"]
