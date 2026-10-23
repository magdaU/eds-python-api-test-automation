import allure


def labels(epic: str, feature: str) -> list:
    """Allure Behaviors labels for a whole test module, used as `pytestmark = labels(...)`."""
    return [allure.epic(epic), allure.feature(feature)]
