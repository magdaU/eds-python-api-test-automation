import pytest
from pytest_bdd import scenarios

from tests.support.allure_labels import labels
from tests.support.attachments import swagger_screenshot  # noqa: F401

pytestmark = [
    *labels("BDD scenarios", "Documented rules"),
    pytest.mark.usefixtures("swagger_screenshot"),
]

scenarios("features/documented_rules.feature")
