import os
import platform
from importlib.metadata import version
from pathlib import Path

TRACKED_PACKAGES = ["pytest", "allure-pytest", "requests", "urllib3", "pydantic", "jsonschema", "hypothesis"]


def build_environment(base_url: str, markexpr: str, ci_env: dict[str, str]) -> dict[str, str]:
    """Key/value pairs for Allure's Environment widget. No host name or IP, only reproducible facts."""
    properties = {
        "Base.URL": base_url,
        "Test.Scope": markexpr or "all (offline + live)",
        "Python": platform.python_version(),
        "OS": platform.system(),
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


def environment_from_session(config) -> None:
    """pytest hook helper: write environment.properties when `--alluredir` is in use."""
    from client.eds_client import BASE_URL

    directory = config.getoption("allure_report_dir", None)
    if directory:
        write_environment(directory, build_environment(BASE_URL, config.option.markexpr, dict(os.environ)))
