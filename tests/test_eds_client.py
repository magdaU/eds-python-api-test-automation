from client.eds_client import EDSApiClient, RETRYABLE_STATUS_CODES


def test_default_retry_configuration():
    client = EDSApiClient()
    adapter = client.session.get_adapter(client.base_url)

    assert adapter.max_retries.total == 3
    assert adapter.max_retries.backoff_factor == 1.0
    assert set(adapter.max_retries.status_forcelist) == set(RETRYABLE_STATUS_CODES)


def test_custom_retry_configuration():
    client = EDSApiClient(max_retries=5, backoff_factor=2.0)
    adapter = client.session.get_adapter(client.base_url)

    assert adapter.max_retries.total == 5
    assert adapter.max_retries.backoff_factor == 2.0
