from typing import Literal

import allure


def labels(epic: str, feature: str, severity: Literal["blocker", "critical", "normal", "minor", "trivial"] = "normal") -> list:
    """Allure Behaviors labels and severity for a whole test module, used as `pytestmark = labels(...)`.

    critical: the client or the API contract is broken for every caller. minor: only test tooling or logs are affected.
    """
    return [allure.epic(epic), allure.feature(feature), allure.severity(allure.severity_level(severity))]
