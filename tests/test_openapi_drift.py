"""The client relies on part of the public OpenAPI specification; this notices when EDS stops
documenting it."""

from tests.support.allure_labels import labels
from tests.support.live import (
    live_eds_client,  # noqa: F401
)
from tests.support.openapi import EXPECTED_PARAMETERS, find_drift

pytestmark = labels("Dataset API", "API specification drift", "critical")


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
