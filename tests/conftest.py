import pytest

from client.dataset_api import DatasetApi
from client.eds_client import EDSApiClient
from client.news_api import NewsApi
from tests.support.allure_environment import environment_from_session
from tests.support.datasets import ALL_DATASETS, CO2EMIS_DATASET, ELSPOTPRICES_DATASET
from tests.support.scripted_server import ScriptedServer


def pytest_sessionfinish(session):
    environment_from_session(session)


@pytest.fixture
def scripted_server():
    """Factory for a local HTTP server that answers with the given statuses in order."""
    servers = []

    def start(*statuses, headers=None):
        server = ScriptedServer(list(statuses), headers)
        servers.append(server)
        return server

    yield start
    for server in servers:
        server.close()


@pytest.fixture(scope="session")
def eds_client():
    return EDSApiClient()


@pytest.fixture
def co2_api(eds_client):
    return DatasetApi(eds_client, CO2EMIS_DATASET.name)


@pytest.fixture
def elspotprices_api(eds_client):
    return DatasetApi(eds_client, ELSPOTPRICES_DATASET.name)


@pytest.fixture
def news_api(eds_client):
    return NewsApi(eds_client)


@pytest.fixture(params=ALL_DATASETS, ids=lambda dataset: dataset.name)
def dataset(request):
    return request.param


@pytest.fixture
def dataset_api(eds_client, dataset):
    return DatasetApi(eds_client, dataset.name)


@pytest.fixture
def co2_response(co2_api):
    return co2_api.get(limit=1)


@pytest.fixture
def elspotprices_response(elspotprices_api):
    return elspotprices_api.get(limit=1)
