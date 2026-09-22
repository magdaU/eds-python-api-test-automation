import requests

BASE_URL = "https://api.energidataservice.dk/dataset/CO2Emis"


def test_status_code_ok():
    response = requests.get(BASE_URL)
    assert response.status_code == 200


def test_response_is_json():
    response = requests.get(BASE_URL)
    assert response.headers["Content-Type"].startswith("application/json")
    response.json()


def test_response_structure():
    response = requests.get(BASE_URL)
    body = response.json()

    assert "records" in body
    assert "total" in body
    assert isinstance(body["records"], list)


def test_limit_parameter_returns_expected_number_of_records():
    limit = 5
    response = requests.get(BASE_URL, params={"limit": limit})
    body = response.json()

    assert response.status_code == 200
    assert len(body["records"]) == limit


def test_filter_parameter_returns_matching_records():
    price_area = "DK1"
    response = requests.get(
        BASE_URL,
        params={"filter": f'{{"PriceArea":"{price_area}"}}', "limit": 5},
    )
    body = response.json()

    assert response.status_code == 200
    assert all(record["PriceArea"] == price_area for record in body["records"])
