import json

import jsonschema


def assert_matches_schema(instance, schema_filename):
    with open(f"schemas/{schema_filename}") as f:
        schema = json.load(f)

    jsonschema.validate(instance=instance, schema=schema)


def assert_all_match_schema(items, schema_filename):
    for item in items:
        assert_matches_schema(item, schema_filename)
