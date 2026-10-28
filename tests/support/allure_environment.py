import os
import platform
from importlib.metadata import version
from pathlib import Path

from client.eds_client import BASE_URL

TRACKED_PACKAGES = ["pytest", "allure-pytest", "requests", "urllib3", "pydantic", "jsonschema", "hypothesis"]
# the outcomes Allure groups into failure categories
CATEGORIZED_OUTCOMES = ("failed", "error", "skipped")


def categories_note(categorized_tests: int) -> str:
    """Why the Categories widgets look the way they do, so that an empty widget doesn't read as something missing."""
    if categorized_tests == 0:
        return "none - no test failed, broke or was skipped, so Categories and Categories trend are empty by design"
    return f"{categorized_tests} test(s) failed, broke or were skipped - see the Categories page for how they are classified"


def build_environment(base_url: str, markexpr: str, ci_env: dict[str, str], categorized_tests: int) -> dict[str, str]:
    """Key/value pairs for Allure's Environment widget. No host name or IP, only reproducible facts."""
    properties = {
        "Base.URL": base_url,
        "Test.Scope": markexpr or "all (offline + live)",
        "Python": platform.python_version(),
        "OS": platform.system(),
        "Categories": categories_note(categorized_tests),
    }
    for package in TRACKED_PACKAGES:
        properties[package] = version(package)
    if ci_env.get("GITHUB_ACTIONS"):
        properties["CI.Branch"] = ci_env.get("GITHUB_REF_NAME", "")
        properties["CI.Commit"] = ci_env.get("GITHUB_SHA", "")[:7]
        properties["CI.Run"] = ci_env.get("GITHUB_RUN_NUMBER", "")
    return properties


def write_environment(directory: str, properties: dict[str, str]) -> None:
    Path(directory).mkdir(parents=True, exist_ok=True)
    lines = [f"{key}={value}" for key, value in properties.items()]
    Path(directory, "environment.properties").write_text("\n".join(lines) + "\n", encoding="utf-8")


def count_categorized(session) -> int:
    """Tests of this session that Allure will put into a failure category."""
    stats = getattr(session.config.pluginmanager.get_plugin("terminalreporter"), "stats", {})
    return sum(len(stats.get(outcome, [])) for outcome in CATEGORIZED_OUTCOMES)


def environment_from_session(session) -> None:
    """pytest hook helper: write environment.properties when `--alluredir` is in use."""
    config = session.config
    directory = config.getoption("allure_report_dir", None)
    if directory:
        properties = build_environment(BASE_URL, config.option.markexpr, dict(os.environ), count_categorized(session))
        write_environment(directory, properties)
