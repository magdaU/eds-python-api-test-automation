import pytest

from client.dataset_api import DatasetApi
from client.eds_client import EDSApiClient
from client.news_api import NewsApi
from tests.support.allure_environment import environment_from_session
from tests.support.datasets import ALL_DATASETS, CO2EMIS_DATASET, DAYAHEADPRICES_DATASET
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
    return DatasetApi(eds_client, CO2EMIS_DATASET.name, CO2EMIS_DATASET.model)


@pytest.fixture
def dayaheadprices_api(eds_client):
    return DatasetApi(eds_client, DAYAHEADPRICES_DATASET.name, DAYAHEADPRICES_DATASET.model)


@pytest.fixture
def news_api(eds_client):
    return NewsApi(eds_client)


@pytest.fixture(params=ALL_DATASETS, ids=lambda dataset: dataset.name)
def dataset(request):
    return request.param


@pytest.fixture
def dataset_api(eds_client, dataset):
    return DatasetApi(eds_client, dataset.name, dataset.model)


@pytest.fixture
def co2_response(co2_api):
    return co2_api.get(limit=1)


@pytest.fixture(scope="session")
def dayaheadprices_latest(eds_client):
    """The only live query a test run sends to DayAheadPrices, shared by every live test that needs its data."""
    return DatasetApi(eds_client, DAYAHEADPRICES_DATASET.name).get(**DAYAHEADPRICES_LIVE_QUERY)
