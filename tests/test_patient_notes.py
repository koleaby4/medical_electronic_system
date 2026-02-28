from fastapi.testclient import TestClient


def test_create_and_update_patient_with_notes(client: TestClient):
    # 1. Create a new patient with notes
    form_data = {
        "title": "Mr",
        "first_name": "Test",
        "last_name": "Patient",
        "sex": "male",
        "dob": "2000-01-01",
        "email": "test@patient.com",
        "phone": "1234567890",
        "notes": "Initial notes for the patient.",
        "line_1": "123 Test St",
        "town": "Test Town",
        "postcode": "TE1 1ST",
        "country": "United Kingdom",
    }

    # POST to /patients
    resp = client.post("/patients", data=form_data, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.text
    assert "Initial notes for the patient." in html

    # Extract patient_id from the redirect URL if possible, or just look at the page
    # The RedirectResponse in routes/patients.py redirects to /patients/{saved_patient.patient_id}
    # Since we used follow_redirects=True, we are at /patients/{id}
    patient_url = str(resp.url)
    patient_id = patient_url.split("/")[-1]

    # 2. Update the patient's notes
    update_data = form_data.copy()
    update_data["notes"] = "Updated notes for the patient."
    update_data["title"] = "Dr"  # Change something else too

    # PUT to /patients/{id}
    resp = client.put(f"/patients/{patient_id}", data=update_data, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.text
    assert "Updated notes for the patient." in html
    assert "Dr" in html
    assert "Initial notes for the patient." not in html

    # 3. Check if notes are optional (clear them)
    clear_notes_data = update_data.copy()
    clear_notes_data["notes"] = ""

    resp = client.put(f"/patients/{patient_id}", data=clear_notes_data, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.text
    # We should probably check the edit form to see if it's empty
    resp = client.get(f"/patients/{patient_id}/edit")
    assert resp.status_code == 200
    assert (
        'placeholder="Notes"></textarea>' in resp.text
        or 'name="notes" id="notes" class="form-control" rows="3" placeholder="Notes"></textarea>' in resp.text
    )


def test_edit_form_populates_notes(client: TestClient):
    # 1. Create a patient with notes
    form_data = {
        "title": "Mr",
        "first_name": "Edit",
        "last_name": "Test",
        "sex": "male",
        "dob": "1990-01-01",
        "email": "edit@test.com",
        "phone": "1234567890",
        "notes": "Some important notes about this patient.",
        "line_1": "123 Main St",
        "town": "Anytown",
        "postcode": "AN1 1ST",
        "country": "United Kingdom",
    }
    resp = client.post("/patients", data=form_data, follow_redirects=True)
    assert resp.status_code == 200

    patient_url = str(resp.url)
    patient_id = patient_url.split("/")[-1]

    # 2. Get the edit form
    resp = client.get(f"/patients/{patient_id}/edit")
    assert resp.status_code == 200
    assert "Some important notes about this patient." in resp.text
