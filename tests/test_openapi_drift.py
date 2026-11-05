"""The client relies on part of the public OpenAPI specification; this notices when EDS stops
documenting it."""

import pytest
import requests

import allure
from client.eds_client import DEFAULT_TIMEOUT
from tests.support.allure_labels import labels
from tests.support.live import (
    TRANSIENT_NETWORK_ERRORS,
    live_eds_client,  # noqa: F401
)
from tests.support.openapi import EXPECTED_PARAMETERS, SPEC_PATH, find_drift

pytestmark = labels("Dataset API", "API specification drift", "critical")


@pytest.mark.live
@pytest.mark.flaky(reruns=1, reruns_delay=5, only_rerun=TRANSIENT_NETWORK_ERRORS)
@allure.epic("Live API")
def test_whenComparingWithThePublishedSpecification_thenEveryOperationTheClientUsesIsDocumented(
    eds_client,
):
    # arrange
    # plain requests on purpose: the client's retry and parsing would hide a specification that
    # changed
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
                "get": {
                    "parameters": [
                        {
                            "name": "datasetName",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "string", "format": "int32"},
                        },
                    ]
                }
            },
            "/meta/dataset/{datasetName}": {
                "get": {
                    "parameters": [
                        {
                            "name": "datasetName",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ]
                }
            },
        }
    }
    expected = {
        key: EXPECTED_PARAMETERS[key]
        for key in ("/dataset/{datasetName}", "/meta/Dataset/{datasetName}", "/News/calendar")
    }

    # act
    problems = find_drift(spec, expected)

    # assert
    assert problems == [
        "GET /dataset/{datasetName} no longer documents the parameter filter",
        "GET /dataset/{datasetName}: the parameter limit is documented as string, not integer",
        "GET /dataset/{datasetName} no longer documents the parameter offset",
        "GET /dataset/{datasetName} no longer documents the parameter sort",
        "GET /News/calendar is no longer documented",
    ]
