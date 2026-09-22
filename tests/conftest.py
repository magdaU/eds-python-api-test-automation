import pytest

from client.eds_client import EDSApiClient

DATASET = "CO2Emis"


@pytest.fixture(scope="session")
def eds_client():
    return EDSApiClient()


@pytest.fixture
def co2_response(eds_client):
    return eds_client.get_dataset(DATASET)
