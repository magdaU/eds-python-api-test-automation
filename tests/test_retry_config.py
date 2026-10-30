import logging

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


def test_givenBaseUrlWithTrailingSlash_whenResolvingOverriddenDataset_thenOverrideStillApplies():
    # arrange
    client = EDSApiClient(
        base_url="https://api.energidataservice.dk/",
        retry=RetryConfig(max_retries=3),
        dataset_overrides={"DayAheadPrices": RetryConfig(max_retries=5)},
    )

    # act
    overridden = _retry_of(client, "DayAheadPrices")

    # assert
    assert overridden.total == 5


def test_givenDatasetOverrideWithJitter_whenResolvingDatasets_thenOnlyThatDatasetHasJitter():
    # arrange
    client = EDSApiClient(
        retry=RetryConfig(backoff_jitter=0.0),
        dataset_overrides={"DayAheadPrices": RetryConfig(backoff_jitter=0.5)},
    )

    # act
    overridden = _retry_of(client, "DayAheadPrices")
    default = _retry_of(client, "CO2Emis")

    # assert
    assert overridden.backoff_jitter == 0.5
    assert default.backoff_jitter == 0.0


def test_givenExcessiveMaxRetries_whenCreatingClient_thenWarningIsLogged(caplog):
    # act
    with caplog.at_level(logging.WARNING):
        EDSApiClient(retry=RetryConfig(max_retries=SANE_MAX_RETRIES + 1))

    # assert
    assert any(record.levelname == "WARNING" for record in caplog.records)


def test_givenDatasetOverrideWithExcessiveMaxRetries_whenCreatingClient_thenWarningIsLogged(caplog):
    # act
    with caplog.at_level(logging.WARNING):
        EDSApiClient(dataset_overrides={"DayAheadPrices": RetryConfig(max_retries=SANE_MAX_RETRIES + 1)})

    # assert
    assert any(record.levelname == "WARNING" for record in caplog.records)


def test_givenSaneMaxRetries_whenCreatingClient_thenNoWarningIsLogged(caplog):
    # act
    with caplog.at_level(logging.WARNING):
        EDSApiClient(retry=RetryConfig(max_retries=SANE_MAX_RETRIES))

    # assert
    assert caplog.records == []
