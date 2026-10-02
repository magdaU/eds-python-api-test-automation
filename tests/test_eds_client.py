from client.eds_client import EDSApiClient, RETRYABLE_STATUS_CODES


def test_whenCreatingClientWithDefaults_thenDefaultRetryConfigurationIsApplied():
    # arrange
    client = EDSApiClient()

    # act
    adapter = client.session.get_adapter(client.base_url)

    # assert
    assert adapter.max_retries.total == 3
    assert adapter.max_retries.backoff_factor == 1.0
    assert set(adapter.max_retries.status_forcelist) == set(RETRYABLE_STATUS_CODES)


def test_givenCustomRetrySettings_whenCreatingClient_thenTheyAreApplied():
    # arrange
    client = EDSApiClient(max_retries=5, backoff_factor=2.0)

    # act
    adapter = client.session.get_adapter(client.base_url)

    # assert
    assert adapter.max_retries.total == 5
    assert adapter.max_retries.backoff_factor == 2.0
