import logging

DATASET = "CO2Emis"
BASE_URL = "https://api.energidataservice.dk"


def test_retryable_status_logs_warning(eds_client, requests_mock, caplog):
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", status_code=429)

    with caplog.at_level(logging.WARNING):
        eds_client.get_dataset(DATASET)

    assert any("429" in record.message for record in caplog.records)
    assert any(record.levelname == "WARNING" for record in caplog.records)


def test_successful_request_does_not_log_warning(eds_client, requests_mock, caplog):
    requests_mock.get(f"{BASE_URL}/dataset/{DATASET}", status_code=200, json={"records": [], "total": 0})

    with caplog.at_level(logging.WARNING):
        eds_client.get_dataset(DATASET)

    assert caplog.records == []
