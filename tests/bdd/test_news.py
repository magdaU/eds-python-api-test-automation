from pytest_bdd import scenarios

from tests.support.allure_labels import labels

pytestmark = labels("BDD scenarios", "News")

scenarios("features/news.feature")
