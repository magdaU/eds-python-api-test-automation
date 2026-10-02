import logging


def test_givenRetryableStatus_whenGettingDataset_thenWarningIsLogged(co2_api, requests_mock, caplog):
    # arrange
    requests_mock.get(co2_api.url, status_code=429)

    # act
    with caplog.at_level(logging.WARNING):
        co2_api.get()

    # assert
    assert any("429" in record.message for record in caplog.records)
    assert any(record.levelname == "WARNING" for record in caplog.records)


def test_givenSuccessfulResponse_whenGettingDataset_thenNoWarningIsLogged(co2_api, requests_mock, caplog):
    # arrange
    requests_mock.get(co2_api.url, status_code=200, json={"records": [], "total": 0})

    # act
    with caplog.at_level(logging.WARNING):
        co2_api.get()

    # assert
    assert caplog.records == []
