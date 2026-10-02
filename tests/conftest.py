import pytest

from client.dataset_api import DatasetApi
from client.eds_client import EDSApiClient
from client.news_api import NewsApi
from tests.support.datasets import ALL_DATASETS, CO2EMIS_DATASET, ELSPOTPRICES_DATASET


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
    return co2_api.get()


@pytest.fixture
def elspotprices_response(elspotprices_api):
    return elspotprices_api.get()
