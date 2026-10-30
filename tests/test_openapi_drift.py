"""The client relies on part of the public OpenAPI specification; this notices when EDS stops documenting it."""

import pytest
import requests

import allure
from client.eds_client import DEFAULT_TIMEOUT
from tests.support.allure_labels import labels
from tests.support.live import TRANSIENT_NETWORK_ERRORS
from tests.support.openapi import SPEC_PATH, USED_OPERATIONS, find_drift

pytestmark = labels("Dataset API", "API specification drift", "critical")


@pytest.mark.live
@pytest.mark.flaky(reruns=1, reruns_delay=5, only_rerun=TRANSIENT_NETWORK_ERRORS)
@allure.epic("Live API")
def test_whenComparingWithThePublishedSpecification_thenEveryOperationTheClientUsesIsStillDocumented(eds_client):
    # arrange
    response = requests.get(f"{eds_client.base_url}{SPEC_PATH}", timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()

    # act
    problems = find_drift(response.json())

    # assert
    assert problems == []


def test_givenSpecificationWithoutAPathAndAParameter_whenLookingForDrift_thenBothAreReported():
    # arrange
    spec = {
        "paths": {
            "/dataset/{datasetName}": {
                "get": {"parameters": [{"name": "datasetName"}, {"name": "limit", "schema": {"type": "string"}}]}
            },
            "/meta/dataset/{datasetName}": {"get": {"parameters": [{"name": "datasetName"}]}},
        }
    }
    used = {key: USED_OPERATIONS[key] for key in ("/dataset/{datasetName}", "/meta/Dataset/{datasetName}", "/News/calendar")}

    # act
    problems = find_drift(spec, used)

    # assert
    assert problems == [
        "GET /dataset/{datasetName} no longer documents the parameter filter",
        "GET /dataset/{datasetName} no longer documents the parameter offset",
        "GET /dataset/{datasetName} no longer documents the parameter sort",
        "GET /dataset/{datasetName}: the parameter limit is documented as string, not integer",
        "GET /News/calendar is no longer documented",
    ]
