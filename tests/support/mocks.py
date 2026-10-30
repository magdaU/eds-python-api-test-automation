import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

MOCKS_DIR = Path(__file__).resolve().parents[1] / "mocks"


def load_mock(filename):
    return json.loads((MOCKS_DIR / filename).read_text(encoding="utf-8"))


def records_response(records):
    return {"records": records, "total": len(records)}


def sent_path(requests_mock):
    """Path of the last mocked request, exactly as it was sent (percent-encoding preserved)."""
    return urlparse(requests_mock.last_request.url).path


def sent_query(requests_mock):
    """Query parameters of the last mocked request, with their original case preserved."""
    return parse_qs(urlparse(requests_mock.last_request.url).query)
