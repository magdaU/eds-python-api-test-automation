import logging

import pytest
import requests

from client.eds_client import SANE_MAX_RETRIES, EDSApiClient, RetryConfig
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "Retry configuration")


def _retry_of(client, dataset):
    return client.session.get_adapter(client.dataset_url(dataset)).max_retries


def test_givenDatasetOverride_whenResolvingDatasets_thenOverrideAppliesOnlyToThatDataset():
    # arrange
    client = EDSApiClient(
        retry=RetryConfig(max_retries=3, backoff_factor=1.0),
        dataset_overrides={"DayAheadPrices": RetryConfig(max_retries=5, backoff_factor=2.0)},
    )

    # act
    overridden = _retry_of(client, "DayAheadPrices")
    default = _retry_of(client, "CO2Emis")

    # assert
    assert overridden.total == 5
    assert overridden.backoff_factor == 2.0
    assert default.total == 3
    assert default.backoff_factor == 1.0


def test_givenExcessiveMaxRetries_whenCreatingClient_thenWarningIsLogged(caplog):
    # act
    with caplog.at_level(logging.WARNING):
        EDSApiClient(retry=RetryConfig(max_retries=SANE_MAX_RETRIES + 1))

    # assert
    assert set(caplog.messages) == {
        f"max_retries={SANE_MAX_RETRIES + 1} exceeds the recommended maximum of {SANE_MAX_RETRIES}"
        " -- this risks hammering the public EDS API during an outage or rate limit"
    }


def test_givenDatasetOverride_whenClosingClient_thenItsAdapterIsClosed(monkeypatch):
    # arrange
    client = EDSApiClient(dataset_overrides={"DayAheadPrices": RetryConfig(max_retries=5)})
    adapter = client.session.dataset_adapters[client.dataset_url("DayAheadPrices")]
    closed = []
    monkeypatch.setattr(adapter, "close", lambda: closed.append(True))

    # act
    client.close()

    # assert
    assert closed == [True]


@pytest.mark.parametrize(
    "field", ["max_retries", "backoff_factor", "backoff_jitter", "max_retry_after"]
)
def test_givenNegativeValue_whenCreatingRetryConfig_thenValueErrorNamesField(field):
    # arrange
    settings = {field: -1}

    # act
    with pytest.raises(ValueError, match=field) as error:
        RetryConfig(**settings)

    # assert
    assert f"{field} must not be negative, got -1" in str(error.value)


def test_givenZeroTimeout_whenCreatingClient_thenValueErrorNamesTimeout():
    # act
    with pytest.raises(ValueError, match="timeout") as error:
        EDSApiClient(timeout=0)

    # assert
    assert str(error.value) == "timeout must be positive, got 0"


def test_givenBaseUrlWithUpperCaseHost_whenResolvingOverriddenDataset_thenOverrideStillApplies():
    # arrange
    client = EDSApiClient(
        base_url="https://API.Energidataservice.DK",
        retry=RetryConfig(max_retries=3),
        dataset_overrides={"DayAheadPrices": RetryConfig(max_retries=5)},
    )

    # act
    prepared_url = requests.Request("GET", client.dataset_url("DayAheadPrices")).prepare().url
    overridden = client.session.get_adapter(prepared_url).max_retries

    # assert
    assert prepared_url.startswith("https://api.energidataservice.dk/")
    assert overridden.total == 5


def test_givenDatasetOverride_whenRequestHasQueryString_thenOverrideStillApplies():
    # arrange
    client = EDSApiClient(
        retry=RetryConfig(max_retries=3),
        dataset_overrides={"DayAheadPrices": RetryConfig(max_retries=5)},
    )

    # act
    retry = client.session.get_adapter(
        client.dataset_url("DayAheadPrices") + "?limit=5&offset=10"
    ).max_retries

    # assert
    assert retry.total == 5
