from fastapi.testclient import TestClient


def test_create_patient_with_address_form_and_get_json(client: TestClient, create_patient):
    patient_id = create_patient(
        {
            "first_name": "amy",
            "last_name": "pond",
            "sex": "female",
            "dob": "1989-05-01",
            "email": "amy.pond@example.com",
            "phone": "0700000000",
            # Address via form
            "address_line_1": "Leadworth Cottage",
            "address_line_2": "",
            "address_town": "leadworth",
            "address_postcode": "sw1a1aa",
            "address_country": "united kingdom",
        }
    )

    # Fetch as JSON to assert model fields
    resp = client.get(f"/patients/{patient_id}", headers={"Accept": "application/json"})
    assert resp.status_code == 200
    data = resp.json()

    assert data["first_name"] == "Amy"
    assert data["last_name"] == "Pond"
    # Address should be present and normalized
    addr = data.get("address")
    assert addr is not None
    assert addr["line_1"] == "Leadworth Cottage"
    # Optional line_2 empty should serialize as None/null
    assert addr.get("line_2") in (None, "")
    assert addr["town"] == "leadworth"
    assert addr["postcode"] == "SW1A 1AA"  # normalized with space and uppercase
    assert addr["country"] == "United Kingdom"  # title-cased/defaulted


def test_update_patient_address_form_and_omit_does_not_delete(client: TestClient, create_patient):
    # Create without address
    patient_id = create_patient({"first_name": "rory", "last_name": "williams"})

    # Update to add address
    update_form = {
        "title": "Mr",
        "first_name": "rory",
        "middle_name": "",
        "last_name": "williams",
        "sex": "male",
        "dob": "1990-01-02",
        "email": "rory.williams@example.com",
        "phone": "+1-555-0101",
        "address_line_1": "Some Street 1",
        "address_line_2": "Flat B",
        "address_town": "Leadworth",
        "address_postcode": "EC1A1BB",
        "address_country": "UNITED KINGDOM",
    }
    resp = client.put(f"/patients/{patient_id}", data=update_form)
    assert resp.status_code in (200, 303)

    # Verify address saved
    resp = client.get(f"/patients/{patient_id}", headers={"Accept": "application/json"})
    data = resp.json()
    addr = data["address"]
    assert addr["line_1"] == "Some Street 1"
    assert addr["line_2"] == "Flat B"
    assert addr["town"] == "Leadworth"
    assert addr["postcode"] == "EC1A 1BB"
    assert addr["country"] == "United Kingdom"

    # Next update: omit address fields entirely; it should remain unchanged
    resp = client.put(
        f"/patients/{patient_id}",
        data={
            "title": "Mr",
            "first_name": "rory",
            "last_name": "williams",
            "sex": "male",
            "dob": "1990-01-02",
            "email": "rory.williams@example.com",
            "phone": "+1-555-0101",
        },
    )
    assert resp.status_code in (200, 303)

    resp = client.get(f"/patients/{patient_id}", headers={"Accept": "application/json"})
    data = resp.json()
    addr_after = data["address"]
    assert addr_after == addr  # unchanged


def test_create_patient_with_address_json_nested(client: TestClient):
    payload = {
        "title": "Ms",
        "first_name": "clara",
        "last_name": "oswald",
        "sex": "female",
        "dob": "1986-11-23",
        "email": "clara@example.com",
        "phone": "0700000001",
        "address": {
            "line_1": "Flat 23",
            "line_2": None,
            "town": "Blackpool",
            "postcode": "w1a0ax",
            "country": "united kingdom",
        },
    }

    resp = client.post("/patients", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["first_name"] == "Clara"
    addr = data.get("address")
    assert addr is not None
    assert addr["postcode"] == "W1A 0AX"
    assert addr["country"] == "United Kingdom"

    # Fetch via GET to ensure persisted
    patient_id = data["patient_id"]
    resp = client.get(f"/patients/{patient_id}", headers={"Accept": "application/json"})
    assert resp.status_code == 200
    persisted = resp.json()["address"]
    assert persisted["line_1"] == "Flat 23"
    assert persisted["postcode"] == "W1A 0AX"


def test_create_patient_with_address_json_flat_fields(client: TestClient):
    payload = {
        "title": "Mr",
        "first_name": "john",
        "last_name": "smith",
        "sex": "male",
        "dob": "1980-01-01",
        "email": "js@example.com",
        "phone": "0000",
        # flat address fields supported by API
        "address_line_1": "10 Downing St",
        "address_town": "London",
        "address_postcode": "sw1a2aa",
        "address_country": "united kingdom",
    }
    resp = client.post("/patients", json=payload)
    assert resp.status_code == 201
    data = resp.json()
    addr = data.get("address")
    assert addr is not None
    assert addr["line_1"] == "10 Downing St"
    assert addr["town"] == "London"
    assert addr["postcode"] == "SW1A 2AA"
    assert addr["country"] == "United Kingdom"
