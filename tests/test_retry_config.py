import logging

from client.eds_client import EDSApiClient, BASE_URL, SANE_MAX_RETRIES


def test_default_retry_applies_to_any_dataset():
    client = EDSApiClient(max_retries=3, backoff_factor=1.0, backoff_jitter=0.0)

    adapter = client.session.get_adapter(f"{BASE_URL}/dataset/CO2Emis")

    assert adapter.max_retries.total == 3
    assert adapter.max_retries.backoff_factor == 1.0
    assert adapter.max_retries.backoff_jitter == 0.0


def test_dataset_override_applies_only_to_that_dataset():
    client = EDSApiClient(
        max_retries=3,
        backoff_factor=1.0,
        dataset_overrides={"Elspotprices": {"max_retries": 5, "backoff_factor": 2.0}},
    )

    overridden_adapter = client.session.get_adapter(f"{BASE_URL}/dataset/Elspotprices")
    default_adapter = client.session.get_adapter(f"{BASE_URL}/dataset/CO2Emis")

    assert overridden_adapter.max_retries.total == 5
    assert overridden_adapter.max_retries.backoff_factor == 2.0
    assert default_adapter.max_retries.total == 3
    assert default_adapter.max_retries.backoff_factor == 1.0


def test_backoff_jitter_is_configured_on_the_retry_object():
    client = EDSApiClient(backoff_jitter=0.5)

    adapter = client.session.get_adapter(f"{BASE_URL}/dataset/CO2Emis")

    assert adapter.max_retries.backoff_jitter == 0.5


def test_dataset_override_can_set_its_own_jitter():
    client = EDSApiClient(
        backoff_jitter=0.0,
        dataset_overrides={"Elspotprices": {"backoff_jitter": 0.5}},
    )

    overridden_adapter = client.session.get_adapter(f"{BASE_URL}/dataset/Elspotprices")
    default_adapter = client.session.get_adapter(f"{BASE_URL}/dataset/CO2Emis")

    assert overridden_adapter.max_retries.backoff_jitter == 0.5
    assert default_adapter.max_retries.backoff_jitter == 0.0


def test_excessive_max_retries_logs_warning(caplog):
    with caplog.at_level(logging.WARNING):
        EDSApiClient(max_retries=SANE_MAX_RETRIES + 1)

    assert any(record.levelname == "WARNING" for record in caplog.records)


def test_dataset_override_with_excessive_max_retries_logs_warning(caplog):
    with caplog.at_level(logging.WARNING):
        EDSApiClient(dataset_overrides={"Elspotprices": {"max_retries": SANE_MAX_RETRIES + 1}})

    assert any(record.levelname == "WARNING" for record in caplog.records)


def test_sane_max_retries_does_not_log_warning(caplog):
    with caplog.at_level(logging.WARNING):
        EDSApiClient(max_retries=SANE_MAX_RETRIES)

    assert caplog.records == []
