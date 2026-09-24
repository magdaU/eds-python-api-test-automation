import requests

DATASET = "CO2Emis"
BASE_URL = "https://api.energidataservice.dk"

# requests_mock replaces how the session dispatches requests entirely, so the
# custom HTTPAdapter/Retry mounted on EDSApiClient's session never runs against
# a mocked response (verified: any mocked status code yields call_count == 1,
# retryable or not). Retry *configuration* is covered at the unit level in
# test_eds_client.py instead of end-to-end here.


def test_invalid_dataset_returns_400(eds_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/dataset/InvalidDataset", status_code=400, json={"error": "invalid dataset"})

    response = eds_client.get_dataset("InvalidDataset")

    assert response.status_code == 400


def test_unknown_path_returns_404(eds_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", status_code=404)

    response = eds_client.get_dataset(DATASET)

    assert response.status_code == 404


def test_connection_timeout_raises(eds_client, requests_mock):
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", exc=requests.exceptions.ConnectTimeout)

    try:
        eds_client.get_dataset(DATASET)
        assert False, "expected ConnectTimeout to be raised"
    except requests.exceptions.ConnectTimeout:
        pass
