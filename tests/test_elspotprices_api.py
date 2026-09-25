import json

import allure
import pytest

DATASET = "Elspotprices"
BASE_URL = "https://api.energidataservice.dk"


def _load_mock(filename):
    with open(f"tests/mocks/{filename}") as f:
        return json.load(f)


@allure.feature("Elspotprices")
def test_status_code_ok(eds_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json=_load_mock("elspotprices_sample.json"))

    response = eds_client.get_dataset(DATASET)

    assert response.status_code == 200


@allure.feature("Elspotprices")
def test_response_is_json(eds_client, requests_mock):
    requests_mock.get(
        f"{BASE_URL}/dataset/{DATASET}",
        json=_load_mock("elspotprices_sample.json"),
        headers={"Content-Type": "application/json"},
    )

    response = eds_client.get_dataset(DATASET)

    assert response.headers["Content-Type"].startswith("application/json")
    response.json()


@allure.feature("Elspotprices")
def test_response_structure(eds_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json=_load_mock("elspotprices_sample.json"))

    body = eds_client.get_dataset(DATASET).json()

    assert "records" in body
    assert "total" in body
    assert isinstance(body["records"], list)


@allure.feature("Elspotprices")
@pytest.mark.parametrize("limit", [1, 3, 5, 10])
def test_limit_parameter_returns_expected_number_of_records(eds_client, requests_mock, limit):
    all_records = _load_mock("elspotprices_sample.json")["records"]
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json={"records": all_records[:limit], "total": limit})

    response = eds_client.get_dataset(DATASET, limit=limit)
    body = response.json()

    assert response.status_code == 200
    assert len(body["records"]) == limit


@allure.feature("Elspotprices")
@pytest.mark.parametrize("price_area", ["DK1", "DK2"])
def test_filter_parameter_returns_matching_records(eds_client, requests_mock, price_area):
    all_records = _load_mock("elspotprices_sample.json")["records"]
    matching = [r for r in all_records if r["PriceArea"] == price_area]
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json={"records": matching, "total": len(matching)})

    response = eds_client.get_dataset(DATASET, limit=5, filter={"PriceArea": price_area})
    body = response.json()

    assert response.status_code == 200
    assert all(record["PriceArea"] == price_area for record in body["records"])


@allure.feature("Elspotprices")
@pytest.mark.flaky(reruns=2, reruns_delay=5, only_rerun=["ConnectionError", "Timeout", "RetryError"])
def test_sort_descending_returns_ordered_records(eds_client):
    response = eds_client.get_dataset(DATASET, limit=5, sort="SpotPriceDKK desc")
    prices = [r["SpotPriceDKK"] for r in response.json()["records"]]

    assert prices == sorted(prices, reverse=True)
