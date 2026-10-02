import json


def load_mock(filename):
    with open(f"tests/mocks/{filename}") as f:
        return json.load(f)


def records_response(records):
    return {"records": records, "total": len(records)}
