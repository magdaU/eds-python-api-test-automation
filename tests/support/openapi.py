"""What the client relies on in the public OpenAPI specification of the EDS API, and a check that it
is still documented."""

from typing import Any

SPEC_PATH = "/swagger/public/swagger.json"
PARAMETER_REF_PREFIX = "#/components/parameters/"

# Path as the specification writes it -> HTTP method -> parameter name -> what the client relies on:
# "in" (path, query, header or cookie), "type", "format" (optional) and "required".
EXPECTED_PARAMETERS: dict[str, dict[str, dict[str, dict[str, Any]]]] = {
    "/dataset/{datasetName}": {
        "get": {
            "datasetName": {"in": "path", "type": "string", "required": True},
            "limit": {"in": "query", "type": "integer", "format": "int32", "required": False},
            "offset": {"in": "query", "type": "integer", "format": "int32", "required": False},
            "sort": {"in": "query", "type": "string", "required": False},
            "filter": {"in": "query", "type": "string", "required": False},
        }
    },
    "/meta/Dataset/{datasetName}": {
        "get": {"datasetName": {"in": "path", "type": "string", "required": True}}
    },
    "/News": {"get": {}},
    "/News/actual": {"get": {"category": {"in": "query", "type": "string", "required": False}}},
    "/News/calendar": {"get": {}},
    "/News/archived": {
        "get": {"date": {"in": "query", "type": "string", "format": "date-time", "required": False}}
    },
}


def find_drift(
    spec: dict, expected: dict[str, dict[str, dict[str, dict[str, Any]]]] = EXPECTED_PARAMETERS
) -> list[str]:
    """What the client relies on but the specification no longer documents; empty when nothing
    drifted.

    Paths are compared without regard to case: the client calls `/meta/dataset/...`, the
    specification writes `/meta/Dataset/...`.
    """
    items_by_path = {path.lower(): item for path, item in spec.get("paths", {}).items()}
    problems: list[str] = []
    for path, operations in expected.items():
        for method, expected_parameters in operations.items():
            path_item = items_by_path.get(path.lower(), {})
            operation = path_item.get(method)
            label = f"{method.upper()} {path}"
            if operation is None:
                problems.append(f"{label} is no longer documented")
                continue
            parameters = _effective_parameters(spec, path_item, operation)
            for name, wanted in sorted(expected_parameters.items()):
                problems += _parameter_drift(label, parameters, name, wanted)
    return problems


def _effective_parameters(spec: dict, path_item: dict, operation: dict) -> list[dict]:
    """The parameters that apply to the operation: those of the path, unless the operation defines
    the same name in the same location (OpenAPI rule)."""
    own = [_resolve(parameter, spec) for parameter in operation.get("parameters", [])]
    own_keys = {(parameter.get("name"), parameter.get("in")) for parameter in own}
    inherited = [
        _resolve(parameter, spec)
        for parameter in path_item.get("parameters", [])
        if (parameter.get("name"), parameter.get("in")) not in own_keys
    ]
    return inherited + own


def _resolve(parameter: dict, spec: dict) -> dict:
    """The parameter itself, or the component it refers to; an unknown reference resolves to an
    empty dict, so the parameter counts as undocumented."""
    if "$ref" not in parameter:
        return parameter
    name = parameter["$ref"].removeprefix(PARAMETER_REF_PREFIX)
    return spec.get("components", {}).get("parameters", {}).get(name, {})


def _parameter_drift(label: str, parameters: list[dict], name: str, wanted: dict) -> list[str]:
    candidates = [parameter for parameter in parameters if parameter.get("name") == name]
    if not candidates:
        return [f"{label} no longer documents the parameter {name}"]
    documented = next((p for p in candidates if p.get("in") == wanted["in"]), candidates[0])
    schema = documented.get("schema", {})
    where = f"{label}: the parameter {name}"
    problems = []
    if documented.get("in") != wanted["in"]:
        problems.append(f"{where} is documented in {documented.get('in')}, not {wanted['in']}")
    if schema.get("type") != wanted["type"]:
        problems.append(f"{where} is documented as {schema.get('type')}, not {wanted['type']}")
    if "format" in wanted and schema.get("format") != wanted["format"]:
        problems.append(
            f"{where} is documented with format {schema.get('format')}, not {wanted['format']}"
        )
    required = bool(documented.get("required", False))
    if required != wanted["required"]:
        problems.append(
            f"{where} is documented with required={required}, not required={wanted['required']}"
        )
    return problems
