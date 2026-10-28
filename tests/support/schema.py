import json
from pathlib import Path

import jsonschema

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"


def assert_matches_schema(instance, schema_filename):
    schema = json.loads((SCHEMAS_DIR / schema_filename).read_text(encoding="utf-8"))

    jsonschema.validate(instance=instance, schema=schema)


def assert_all_match_schema(items, schema_filename):
    for item in items:
        assert_matches_schema(item, schema_filename)
