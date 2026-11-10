from pytest_bdd import scenarios

from tests.support.allure_labels import labels

pytestmark = labels("BDD scenarios", "Documented rules")

scenarios("features/documented_rules.feature")
