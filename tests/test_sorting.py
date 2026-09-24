import json

DATASET = "Elspotprices"
BASE_URL = "https://api.energidataservice.dk"


def _load_mock(filename):
    with open(f"tests/mocks/{filename}") as f:
        return json.load(f)


def test_sort_ascending_returns_ordered_records(eds_client, requests_mock):
    mock_data = _load_mock("elspotprices_sorted.json")
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json=mock_data)

    response = eds_client.get_dataset(DATASET, sort="SpotPriceDKK")
    prices = [r["SpotPriceDKK"] for r in response.json()["records"]]

    assert prices == sorted(prices)


def test_sort_descending_returns_ordered_records(eds_client, requests_mock):
    mock_data = _load_mock("elspotprices_sorted.json")
    descending_records = list(reversed(mock_data["records"]))
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json={"records": descending_records, "total": len(descending_records)})

    response = eds_client.get_dataset(DATASET, sort="SpotPriceDKK desc")
    prices = [r["SpotPriceDKK"] for r in response.json()["records"]]

    assert prices == sorted(prices, reverse=True)


def test_sort_parameter_is_sent(eds_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json={"records": [], "total": 0})

    eds_client.get_dataset(DATASET, sort="SpotPriceDKK desc")

    assert requests_mock.last_request.qs["sort"] == ["spotpricedkk desc"]
