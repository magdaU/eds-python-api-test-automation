import pytest
from hypothesis import settings

from client.eds_client import EDSApiClient
from client.news_api import NewsApi
from client.retry import RetryAfterTooLongError
from tests.support.allure_environment import environment_from_session
from tests.support.datasets import (
    ALL_DATASETS,
    CO2EMIS_DATASET,
    api_for_dataset,
)
from tests.support.fake_eds import FakeEds
from tests.support.scripted_server import ScriptedServer


def pytest_sessionfinish(session):
    environment_from_session(session)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """A live test whose wait the API throttled (refused by the run's retry budget or by the
    `Retry-After` cap) is skipped with the reason, not failed: the API asked us to slow down."""
    outcome = yield
    report = outcome.get_result()
    if item.get_closest_marker("live") is None or call.excinfo is None:
        return
    if not isinstance(call.excinfo.value, RetryAfterTooLongError):
        return
    report.outcome = "skipped"
    report.longrepr = (str(item.path), 0, f"Skipped, API throttled: {call.excinfo.value}")


@pytest.fixture
def scripted_server():
    """Factory for a local HTTP server that answers with the given statuses in order."""
    servers = []

    def start(*statuses, headers=None, delay=0):
        server = ScriptedServer(list(statuses), headers, delay)
        servers.append(server)
        return server

    yield start
    for server in servers:
        server.close()


@pytest.fixture(scope="session")
def eds_client():
    with EDSApiClient() as client:
        yield client


@pytest.fixture
def co2_api(eds_client):
    """For the tests that are about CO2Emis specifically; the others take `dataset_api`."""
    return api_for_dataset(eds_client, CO2EMIS_DATASET)


@pytest.fixture
def eds(requests_mock, eds_client):
    """The EDS API replaced by a fake: register what it answers, read what the client sent."""
    return FakeEds(requests_mock, eds_client)


@pytest.fixture
def news_api(eds_client):
    return NewsApi(eds_client)


@pytest.fixture(params=ALL_DATASETS, ids=lambda dataset: dataset.name)
def dataset(request):
    return request.param


@pytest.fixture
def dataset_api(eds_client, dataset):
    return api_for_dataset(eds_client, dataset)


# Hypothesis settings for every property-based test: 100 examples, no per-example deadline.
settings.register_profile("default", max_examples=100, deadline=None)
settings.load_profile("default")
