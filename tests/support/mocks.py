import json
from pathlib import Path

MOCKS_DIR = Path(__file__).resolve().parents[1] / "mocks"


def load_mock(filename):
    return json.loads((MOCKS_DIR / filename).read_text(encoding="utf-8"))


def records_response(records):
    return {"records": records, "total": len(records)}
