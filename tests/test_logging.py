import logging
import re

import pytest
import requests

from tests.support.allure_labels import labels
from tests.support.scripted_server import api_for

pytestmark = labels("Client library", "Logging", "minor")


def test_givenRetryableStatusPersists_whenRetriesAreExhausted_thenWarningIsLogged(scripted_server, caplog):
    # arrange
    server = scripted_server(429)

    # act
    with caplog.at_level(logging.WARNING), pytest.raises(requests.exceptions.RetryError):
        api_for(server).get()

    # assert
    gave_up = [record.getMessage() for record in caplog.records if "Giving up" in record.getMessage()]
    assert len(gave_up) == 1
    assert server.url in gave_up[0]
    assert "too many 429 error responses" in gave_up[0]


def test_givenSuccessfulResponse_whenGettingDataset_thenOneLineLogsRequestStatusAndDuration(scripted_server, caplog):
    # arrange
    server = scripted_server(200)

    # act
    with caplog.at_level(logging.INFO):
        api_for(server).get(limit=1)

    # assert
    messages = [record.getMessage() for record in caplog.records]
    assert len(messages) == 1
    assert re.fullmatch(rf"GET {re.escape(server.url)}/dataset/CO2Emis params=\{{'limit': 1\}} -> 200 in \d+ ms", messages[0])


def test_givenErrorResponse_whenGettingDataset_thenBodyPreviewIsLogged(scripted_server, caplog):
    # arrange
    server = scripted_server(400)

    # act
    with caplog.at_level(logging.INFO):
        api_for(server).get()

    # assert
    messages = [record.getMessage() for record in caplog.records]
    assert len(messages) == 1
    assert "-> 400 in" in messages[0]
    assert messages[0].endswith('body={"records": [], "total": 0}')


def test_givenRetryAfterHeader_whenServerThrottles_thenWaitAndReasonAreLogged(scripted_server, monkeypatch, caplog):
    # arrange
    server = scripted_server(429, 200, headers={"Retry-After": "2"})
    waits = []
    monkeypatch.setattr("urllib3.util.retry.time.sleep", waits.append)

    # act
    with caplog.at_level(logging.WARNING):
        api_for(server).get()

    # assert
    assert waits == [2]
    assert [record.getMessage() for record in caplog.records] == [
        "Retrying in 2.0 s because the server sent Retry-After (status 429)"
    ]


def test_givenServerErrorWithoutRetryAfter_whenRetrying_thenBackoffWaitIsLogged(scripted_server, monkeypatch, caplog):
    # arrange
    server = scripted_server(503, 200)
    monkeypatch.setattr("urllib3.util.retry.time.sleep", lambda seconds: None)

    # act
    with caplog.at_level(logging.WARNING):
        api_for(server).get()

    # assert
    assert [record.getMessage() for record in caplog.records] == ["Retrying in 0.0 s, backoff (status 503)"]
