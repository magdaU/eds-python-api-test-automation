DATASET = "CO2Emis"


def test_status_code_ok(co2_response):
    assert co2_response.status_code == 200


def test_response_is_json(co2_response):
    assert co2_response.headers["Content-Type"].startswith("application/json")
    co2_response.json()


def test_response_structure(co2_response):
    body = co2_response.json()

    assert "records" in body
    assert "total" in body
    assert isinstance(body["records"], list)


def test_limit_parameter_returns_expected_number_of_records(eds_client):
    limit = 5
    response = eds_client.get_dataset(DATASET, limit=limit)
    body = response.json()

    assert response.status_code == 200
    assert len(body["records"]) == limit


def test_filter_parameter_returns_matching_records(eds_client):
    price_area = "DK1"
    response = eds_client.get_dataset(DATASET, limit=5, filter={"PriceArea": price_area})
    body = response.json()

    assert response.status_code == 200
    assert all(record["PriceArea"] == price_area for record in body["records"])
