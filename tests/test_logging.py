import logging

import pytest
import requests

from tests.support.allure_labels import labels
from tests.support.scripted_server import api_for

pytestmark = labels("Client library", "Logging")


def test_givenRetryableStatusPersists_whenRetriesAreExhausted_thenWarningIsLogged(scripted_server, caplog):
    # arrange
    server = scripted_server(429)

    # act
    with caplog.at_level(logging.WARNING), pytest.raises(requests.exceptions.RetryError):
        api_for(server).get()

    # assert
    warnings = [record for record in caplog.records if record.levelname == "WARNING"]
    assert len(warnings) == 1
    assert server.url in warnings[0].getMessage()
    assert "too many 429 error responses" in warnings[0].getMessage()


def test_givenSuccessfulResponse_whenGettingDataset_thenNoWarningIsLogged(co2_api, requests_mock, caplog):
    # arrange
    requests_mock.get(co2_api.url, status_code=200, json={"records": [], "total": 0})

    # act
    with caplog.at_level(logging.WARNING):
        co2_api.get()

    # assert
    assert caplog.records == []
