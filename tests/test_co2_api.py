from client.eds_client import EDSApiClient

DATASET = "CO2Emis"

client = EDSApiClient()


def test_status_code_ok():
    response = client.get_dataset(DATASET)
    assert response.status_code == 200


def test_response_is_json():
    response = client.get_dataset(DATASET)
    assert response.headers["Content-Type"].startswith("application/json")
    response.json()


def test_response_structure():
    response = client.get_dataset(DATASET)
    body = response.json()

    assert "records" in body
    assert "total" in body
    assert isinstance(body["records"], list)


def test_limit_parameter_returns_expected_number_of_records():
    limit = 5
    response = client.get_dataset(DATASET, limit=limit)
    body = response.json()

    assert response.status_code == 200
    assert len(body["records"]) == limit


def test_filter_parameter_returns_matching_records():
    price_area = "DK1"
    response = client.get_dataset(DATASET, limit=5, filter={"PriceArea": price_area})
    body = response.json()

    assert response.status_code == 200
    assert all(record["PriceArea"] == price_area for record in body["records"])
