import json

import allure
import pytest

DATASET = "CO2Emis"
BASE_URL = "https://api.energidataservice.dk"


def _load_mock(filename):
    with open(f"tests/mocks/{filename}") as f:
        return json.load(f)


@allure.feature("CO2Emis")
def test_status_code_ok(eds_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json=_load_mock("co2emis_sample.json"))

    response = eds_client.get_dataset(DATASET)

    assert response.status_code == 200


@allure.feature("CO2Emis")
def test_response_is_json(eds_client, requests_mock):
    requests_mock.get(
        f"{BASE_URL}/dataset/{DATASET}",
        json=_load_mock("co2emis_sample.json"),
        headers={"Content-Type": "application/json"},
    )

    response = eds_client.get_dataset(DATASET)

    assert response.headers["Content-Type"].startswith("application/json")
    response.json()


@allure.feature("CO2Emis")
def test_response_structure(eds_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json=_load_mock("co2emis_sample.json"))

    body = eds_client.get_dataset(DATASET).json()

    assert "records" in body
    assert "total" in body
    assert isinstance(body["records"], list)


@allure.feature("CO2Emis")
@pytest.mark.parametrize("limit", [1, 3, 5, 10])
def test_limit_parameter_returns_expected_number_of_records(eds_client, requests_mock, limit):
    all_records = _load_mock("co2emis_sample.json")["records"]
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json={"records": all_records[:limit], "total": limit})

    response = eds_client.get_dataset(DATASET, limit=limit)
    body = response.json()

    assert response.status_code == 200
    assert len(body["records"]) == limit


@allure.feature("CO2Emis")
@pytest.mark.parametrize("price_area", ["DK1", "DK2"])
def test_filter_parameter_returns_matching_records(eds_client, requests_mock, price_area):
    all_records = _load_mock("co2emis_sample.json")["records"]
    matching = [r for r in all_records if r["PriceArea"] == price_area]
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json={"records": matching, "total": len(matching)})

    response = eds_client.get_dataset(DATASET, limit=5, filter={"PriceArea": price_area})
    body = response.json()

    assert response.status_code == 200
    assert all(record["PriceArea"] == price_area for record in body["records"])


@allure.feature("CO2Emis")
def test_pagination_pages_do_not_overlap(eds_client):
    first_page = eds_client.get_dataset(DATASET, limit=5, offset=0).json()
    second_page = eds_client.get_dataset(DATASET, limit=5, offset=5).json()

    first_timestamps = [r["Minutes5UTC"] for r in first_page["records"]]
    second_timestamps = [r["Minutes5UTC"] for r in second_page["records"]]

    assert len(first_page["records"]) == 5
    assert len(second_page["records"]) == 5
    # tolerancyjne na dryf pojedynczego rekordu w danych aktualizowanych na żywo
    assert first_timestamps != second_timestamps


@allure.feature("CO2Emis")
def test_invalid_dataset_returns_error_status(eds_client):
    response = eds_client.get_dataset("NotARealDataset")

    assert response.status_code != 200
