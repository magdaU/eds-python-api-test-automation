import json

DATASET = "CO2Emis"
BASE_URL = "https://api.energidataservice.dk"


def _load_mock(filename):
    with open(f"tests/mocks/{filename}") as f:
        return json.load(f)


def test_pages_do_not_overlap(eds_client, requests_mock):
    page1 = _load_mock("co2_page1.json")
    page2 = _load_mock("co2_page2.json")

    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", [
        {"json": page1},
        {"json": page2},
    ])

    first_page = eds_client.get_dataset(DATASET, limit=5, offset=0).json()
    second_page = eds_client.get_dataset(DATASET, limit=5, offset=5).json()

    first_timestamps = {r["Minutes5UTC"] for r in first_page["records"]}
    second_timestamps = {r["Minutes5UTC"] for r in second_page["records"]}

    assert len(first_page["records"]) == 5
    assert len(second_page["records"]) == 5
    assert first_timestamps.isdisjoint(second_timestamps)


def test_offset_parameter_is_sent(eds_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json={"records": [], "total": 0})

    eds_client.get_dataset(DATASET, limit=5, offset=10)

    assert requests_mock.last_request.qs["offset"] == ["10"]


def test_limit_zero_returns_all_records(eds_client, requests_mock):
    all_records = _load_mock("co2_page1.json")["records"] + _load_mock("co2_page2.json")["records"]
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", json={"records": all_records, "total": len(all_records)})

    response = eds_client.get_dataset(DATASET, limit=0)

    assert len(response.json()["records"]) == 10