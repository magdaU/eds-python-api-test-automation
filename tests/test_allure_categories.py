import json
import re
from pathlib import Path

import pytest

from tests.support.allure_labels import labels

pytestmark = labels("Test support", "Allure categories")

CATEGORIES = json.loads((Path(__file__).resolve().parents[1] / "allure" / "categories.json").read_text(encoding="utf-8"))
INFRASTRUCTURE = "Infrastructure problems"
CONTRACT_DRIFT = "Contract drift (schema or model mismatch)"


def category_of(status, message):
    """The first category whose statuses and message pattern match, which is how Allure assigns one."""
    for category in CATEGORIES:
        if status in category["matchedStatuses"] and re.search(category.get("messageRegex", ""), message):
            return category["name"]
    return None


@pytest.mark.parametrize(
    "status, message, expected_category",
    [
        ("broken", "RetryError: Max retries exceeded (Caused by ResponseError('too many 503 error responses'))", INFRASTRUCTURE),
        ("failed", "HTTPError: 429 Client Error: Too Many Requests", INFRASTRUCTURE),
        (
            "broken",
            "RetryAfterTooLongError: The server asked to wait 300 s (Retry-After, status 429), more than the 60 s allowed",
            INFRASTRUCTURE,
        ),
        ("broken", "requests.exceptions.ConnectionError: refused", INFRASTRUCTURE),
        ("failed", "AssertionError: assert 'a' == 'b' at port 42951", "Product defects"),
        ("broken", "KeyError: 4290", CONTRACT_DRIFT),
        ("failed", "jsonschema.exceptions.ValidationError: 'Minutes5UTC' is a required property", CONTRACT_DRIFT),
        ("failed", "AssertionError: assert 1 == 2", "Product defects"),
        ("broken", "TypeError: unsupported operand", "Test defects"),
        ("skipped", "", "Skipped tests"),
    ],
    ids=[
        "retries-exhausted",
        "http-429",
        "retry-after-too-long",
        "connection-refused",
        "digits-of-a-port-are-not-429",
        "digits-in-key-error-are-not-429",
        "schema-violation",
        "plain-assertion",
        "unexpected-error",
        "skipped",
    ],
)
def test_givenFailureMessage_whenCategorizing_thenExpectedCategoryIsAssigned(status, message, expected_category):
    # act
    category = category_of(status, message)

    # assert
    assert category == expected_category
