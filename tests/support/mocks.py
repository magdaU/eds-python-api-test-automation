import json
from urllib.parse import parse_qs, urlparse


def load_mock(filename):
    with open(f"tests/mocks/{filename}") as f:
        return json.load(f)


def records_response(records):
    return {"records": records, "total": len(records)}


def sent_query(requests_mock):
    """Query parameters of the last mocked request, with their original case preserved."""
    return parse_qs(urlparse(requests_mock.last_request.url).query)
