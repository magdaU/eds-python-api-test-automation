import pytest
from hypothesis import settings

from client.dataset_api import DatasetApi
from client.eds_client import EDSApiClient
from client.news_api import NewsApi
from tests.support.allure_environment import environment_from_session
from tests.support.datasets import (
    ALL_DATASETS,
    CO2EMIS_DATASET,
    DAYAHEADPRICES_DATASET,
    api_for_dataset,
)
from tests.support.fake_eds import FakeEds
from tests.support.live import DAYAHEADPRICES_LIVE_QUERY
from tests.support.scripted_server import ScriptedServer


def pytest_sessionfinish(session):
    environment_from_session(session)


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


@pytest.fixture
def co2_response(co2_api):
    return co2_api.get(limit=1)


@pytest.fixture(scope="session")
def dayaheadprices_latest(eds_client):
    """The only live query a test run sends to DayAheadPrices, shared by every live test that needs
    its data."""
    return DatasetApi(eds_client, DAYAHEADPRICES_DATASET.name).get(**DAYAHEADPRICES_LIVE_QUERY)


# Hypothesis settings for every property-based test: 100 examples, no per-example deadline.
settings.register_profile("default", max_examples=100, deadline=None)
settings.load_profile("default")
