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


def test_givenLimitMovedFromQueryToHeader_whenLookingForDrift_thenLocationChangeIsReported():
    # arrange
    spec = _spec_with_get([{**DOCUMENTED_LIMIT, "in": "header"}])

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == [
        "GET /dataset/{datasetName}: the parameter limit is documented in header, not query"
    ]


def test_givenLimitTypeChangedToString_whenLookingForDrift_thenTypeChangeIsReported():
    # arrange
    spec = _spec_with_get([{**DOCUMENTED_LIMIT, "schema": {"type": "string", "format": "int32"}}])

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == [
        "GET /dataset/{datasetName}: the parameter limit is documented as string, not integer"
    ]


def test_givenLimitFormatChangedToInt64_whenLookingForDrift_thenFormatChangeIsReported():
    # arrange
    spec = _spec_with_get([{**DOCUMENTED_LIMIT, "schema": {"type": "integer", "format": "int64"}}])

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == [
        "GET /dataset/{datasetName}: the parameter limit is documented with format int64, not int32"
    ]


def test_givenLimitBecameRequired_whenLookingForDrift_thenRequiredChangeIsReported():
    # arrange
    spec = _spec_with_get([{**DOCUMENTED_LIMIT, "required": True}])

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == [
        "GET /dataset/{datasetName}: the parameter limit is documented with required=True, "
        "not required=False"
    ]


def test_givenEndpointRemoved_whenLookingForDrift_thenItIsReported():
    # arrange
    spec = {"paths": {"/News": {"get": {}}}}

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == ["GET /dataset/{datasetName} is no longer documented"]


def test_givenGetBecamePost_whenLookingForDrift_thenTheMissingMethodIsReported():
    # arrange
    spec = {"paths": {DATASET_PATH: {"post": {"parameters": [DOCUMENTED_LIMIT]}}}}

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == ["GET /dataset/{datasetName} is no longer documented"]


def test_givenLimitDeclaredAtPathLevel_whenLookingForDrift_thenItIsStillFound():
    # arrange
    spec = {"paths": {DATASET_PATH: {"parameters": [DOCUMENTED_LIMIT], "get": {}}}}

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == []


def test_givenOperationRedefinesPathLevelLimit_whenLookingForDrift_thenOperationDefinitionIsUsed():
    # arrange
    path_level_wrong_type = {**DOCUMENTED_LIMIT, "schema": {"type": "string", "format": "int32"}}
    spec = {
        "paths": {
            DATASET_PATH: {
                "parameters": [path_level_wrong_type],
                "get": {"parameters": [DOCUMENTED_LIMIT]},
            }
        }
    }

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == []


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


def test_givenLimitReferencedFromComponents_whenLookingForDrift_thenReferenceIsResolved():
    # arrange
    spec = {
        "paths": {
            DATASET_PATH: {"get": {"parameters": [{"$ref": "#/components/parameters/Limit"}]}}
        },
        "components": {"parameters": {"Limit": DOCUMENTED_LIMIT}},
    }

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == []


def test_givenReferencedLimitHasWrongType_whenLookingForDrift_thenTypeChangeIsReported():
    # arrange
    wrong_limit = {**DOCUMENTED_LIMIT, "schema": {"type": "string", "format": "int32"}}
    spec = {
        "paths": {
            DATASET_PATH: {"get": {"parameters": [{"$ref": "#/components/parameters/Limit"}]}}
        },
        "components": {"parameters": {"Limit": wrong_limit}},
    }

    # act
    problems = find_drift(spec, EXPECTED_LIMIT)

    # assert
    assert problems == [
        "GET /dataset/{datasetName}: the parameter limit is documented as string, not integer"
    ]
