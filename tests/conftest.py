import pytest

from client.eds_client import EDSApiClient

CO2_DATASET = "CO2Emis"
ELSPOTPRICES_DATASET = "Elspotprices"


@pytest.fixture(scope="session")
def eds_client():
    return EDSApiClient()


@pytest.fixture
def co2_response(eds_client):
    return eds_client.get_dataset(CO2_DATASET)


@pytest.fixture
def elspotprices_response(eds_client):
    return eds_client.get_dataset(ELSPOTPRICES_DATASET)
