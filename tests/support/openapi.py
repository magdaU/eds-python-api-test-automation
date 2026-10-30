"""What the client relies on in the public OpenAPI specification of the EDS API, and a check that it is still documented."""

SPEC_PATH = "/swagger/public/swagger.json"

# Path as the specification writes it -> parameters the client sends to it (path or query).
USED_OPERATIONS = {
    "/dataset/{datasetName}": {"datasetName", "limit", "offset", "sort", "filter"},
    "/meta/Dataset/{datasetName}": {"datasetName"},
    "/News": set(),
    "/News/actual": {"category"},
    "/News/calendar": set(),
    "/News/archived": {"date"},
}
INTEGER_PARAMETERS = {"limit", "offset"}


def find_drift(spec: dict, used: dict[str, set[str]] = USED_OPERATIONS) -> list[str]:
    """What the client uses but the specification no longer documents; empty when nothing drifted.

    Paths are compared without regard to case: the client calls `/meta/dataset/...`, the specification writes `/meta/Dataset/...`.
    """
    operations_by_path = {path.lower(): operations for path, operations in spec.get("paths", {}).items()}
    problems = []
    for path, expected in used.items():
        operation = operations_by_path.get(path.lower(), {}).get("get")
        if operation is None:
            problems.append(f"GET {path} is no longer documented")
            continue
        documented = {parameter["name"]: parameter for parameter in operation.get("parameters", [])}
        problems += [f"GET {path} no longer documents the parameter {name}" for name in sorted(expected - documented.keys())]
        for name in sorted(INTEGER_PARAMETERS & expected & documented.keys()):
            kind = documented[name].get("schema", {}).get("type")
            if kind != "integer":
                problems.append(f"GET {path}: the parameter {name} is documented as {kind}, not integer")
    return problems
