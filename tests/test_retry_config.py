import logging

from client.eds_client import EDSApiClient, SANE_MAX_RETRIES


def _retry_of(client, dataset):
    return client.session.get_adapter(client.dataset_url(dataset)).max_retries


def test_givenDefaultRetrySettings_whenResolvingAnyDataset_thenDefaultsApply():
    # arrange
    client = EDSApiClient(max_retries=3, backoff_factor=1.0, backoff_jitter=0.0)

    # act
    retry = _retry_of(client, "CO2Emis")

    # assert
    assert retry.total == 3
    assert retry.backoff_factor == 1.0
    assert retry.backoff_jitter == 0.0


def test_givenDatasetOverride_whenResolvingDatasets_thenOverrideAppliesOnlyToThatDataset():
    # arrange
    client = EDSApiClient(
        max_retries=3,
        backoff_factor=1.0,
        dataset_overrides={"Elspotprices": {"max_retries": 5, "backoff_factor": 2.0}},
    )

    # act
    overridden = _retry_of(client, "Elspotprices")
    default = _retry_of(client, "CO2Emis")

    # assert
    assert overridden.total == 5
    assert overridden.backoff_factor == 2.0
    assert default.total == 3
    assert default.backoff_factor == 1.0


def test_givenBackoffJitter_whenCreatingClient_thenItIsConfiguredOnTheRetryObject():
    # arrange
    client = EDSApiClient(backoff_jitter=0.5)

    # act
    retry = _retry_of(client, "CO2Emis")

    # assert
    assert retry.backoff_jitter == 0.5


def test_givenDatasetOverrideWithJitter_whenResolvingDatasets_thenOnlyThatDatasetHasJitter():
    # arrange
    client = EDSApiClient(
        backoff_jitter=0.0,
        dataset_overrides={"Elspotprices": {"backoff_jitter": 0.5}},
    )

    # act
    overridden = _retry_of(client, "Elspotprices")
    default = _retry_of(client, "CO2Emis")

    # assert
    assert overridden.backoff_jitter == 0.5
    assert default.backoff_jitter == 0.0


def test_givenExcessiveMaxRetries_whenCreatingClient_thenWarningIsLogged(caplog):
    # act
    with caplog.at_level(logging.WARNING):
        EDSApiClient(max_retries=SANE_MAX_RETRIES + 1)

    # assert
    assert any(record.levelname == "WARNING" for record in caplog.records)


def test_givenDatasetOverrideWithExcessiveMaxRetries_whenCreatingClient_thenWarningIsLogged(caplog):
    # act
    with caplog.at_level(logging.WARNING):
        EDSApiClient(dataset_overrides={"Elspotprices": {"max_retries": SANE_MAX_RETRIES + 1}})

    # assert
    assert any(record.levelname == "WARNING" for record in caplog.records)


def test_givenSaneMaxRetries_whenCreatingClient_thenNoWarningIsLogged(caplog):
    # act
    with caplog.at_level(logging.WARNING):
        EDSApiClient(max_retries=SANE_MAX_RETRIES)

    # assert
    assert caplog.records == []
