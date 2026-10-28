from pytest_bdd import scenarios

from tests.support.allure_labels import labels

pytestmark = labels("BDD scenarios", "Dataset queries")

scenarios("features/dataset_queries.feature")
