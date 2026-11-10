"""Parameter drift in the OpenAPI specification: name, location, type, format, required flag,
inheritance from the path and `$ref`. Uses small in-memory specifications only."""

from tests.support.allure_labels import labels
from tests.support.openapi import EXPECTED_PARAMETERS, find_drift

pytestmark = labels("Dataset API", "API specification drift", "critical")

DATASET_PATH = "/dataset/{datasetName}"
LIMIT_EXPECTATION = {"in": "query", "type": "integer", "format": "int32", "required": False}
EXPECTED_LIMIT = {DATASET_PATH: {"get": {"limit": LIMIT_EXPECTATION}}}
DOCUMENTED_LIMIT = {
    "name": "limit",
    "in": "query",
    "required": False,
    "schema": {"type": "integer", "format": "int32"},
}


def _spec_with_get(parameters: list[dict], path: str = DATASET_PATH) -> dict:
    return {"paths": {path: {"get": {"parameters": parameters}}}}


def test_givenLimitRemoved_whenLookingForDrift_thenItIsReported():
    # arrange
    spec = _spec_with_get([])

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == ["GET /dataset/{datasetName} no longer documents the parameter limit"]


def test_givenLimitTypeChangedToString_whenLookingForDrift_thenTypeChangeIsReported():
    # arrange
    spec = _spec_with_get([{**DOCUMENTED_LIMIT, "schema": {"type": "string", "format": "int32"}}])

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == [
        "GET /dataset/{datasetName}: the parameter limit is documented as string, not integer"
    ]


def test_givenEndpointRemoved_whenLookingForDrift_thenItIsReported():
    # arrange
    spec = {"paths": {"/News": {"get": {}}}}

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == ["GET /dataset/{datasetName} is no longer documented"]


def test_givenCorrectContract_whenLookingForDrift_thenNoDriftIsReported():
    # arrange
    spec = {
        "paths": {
            DATASET_PATH: {
                "get": {
                    "parameters": [
                        {
                            "name": "datasetName",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        DOCUMENTED_LIMIT,
                        {
                            "name": "offset",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "format": "int32"},
                        },
                        {"name": "sort", "in": "query", "schema": {"type": "string"}},
                        {"name": "filter", "in": "query", "schema": {"type": "string"}},
                    ]
                }
            },
            "/meta/Dataset/{datasetName}": {
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
            "/News": {"get": {}},
            "/News/actual": {
                "get": {
                    "parameters": [
                        {"name": "category", "in": "query", "schema": {"type": "string"}}
                    ]
                }
            },
            "/News/calendar": {"get": {}},
            "/News/archived": {
                "get": {
                    "parameters": [
                        {
                            "name": "date",
                            "in": "query",
                            "schema": {"type": "string", "format": "date-time"},
                        }
                    ]
                }
            },
        }
    }

    # act
    problems = find_drift(spec, EXPECTED_PARAMETERS)

    # assert
    assert problems == []
