import logging
import re

import pytest
import requests

from tests.support.allure_labels import labels
from tests.support.scripted_server import api_for

pytestmark = labels("Client library", "Logging", "minor")


def test_givenRetryableStatusPersists_whenRetriesAreExhausted_thenWarningIsLogged(
    scripted_server, caplog
):
    # arrange
    server = scripted_server(429)

    # act
    with caplog.at_level(logging.WARNING), pytest.raises(requests.exceptions.RetryError):
        api_for(server).get()

    # assert
    gave_up = [
        record.getMessage() for record in caplog.records if "Giving up" in record.getMessage()
    ]
    assert len(gave_up) == 1
    assert server.url in gave_up[0]
    assert "too many 429 error responses" in gave_up[0]


def test_givenBackoffWithJitter_whenRetrying_thenLoggedWaitIsTheWaitThatHappened(
    scripted_server, caplog
):
    # arrange
    server = scripted_server(503, 503, 200)
    waits = []

    # act
    with caplog.at_level(logging.WARNING):
        api_for(server, max_retries=3, sleep=waits.append, backoff_jitter=50.0).get()

    # assert
    # the first retry has no backoff, so only the second one waits (and adds jitter)
    logged = [
        float(re.search(r"Retrying in ([\d.]+) s", record.getMessage()).group(1))
        for record in caplog.records
    ]
    assert len(waits) == 1
    assert logged == [0.0, round(waits[0], 1)]


def test_givenNothingListening_whenGettingDataset_thenFailureWithUrlAndDurationIsLogged(
    scripted_server, caplog
):
    # arrange
    server = scripted_server(200)
    api = api_for(server, max_retries=0)
    server.close()

    # act
    with caplog.at_level(logging.WARNING), pytest.raises(requests.exceptions.ConnectionError):
        api.get(limit=1)

    # assert
    failures = [
        record.getMessage() for record in caplog.records if "Request failed" in record.getMessage()
    ]
    assert len(failures) == 1
    assert f"{server.url}/dataset/CO2Emis" in failures[0]
    assert "params={'limit': 1}" in failures[0]
    assert re.search(r" after \d+ ms: ", failures[0])
