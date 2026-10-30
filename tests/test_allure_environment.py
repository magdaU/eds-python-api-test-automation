import platform
from importlib.metadata import version

from tests.support.allure_environment import (
    TRACKED_PACKAGES,
    build_environment,
    categories_note,
    count_categorized,
    write_environment,
)
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "Allure environment", "minor")


def test_givenCiEnvironment_whenBuildingEnvironment_thenEveryFieldIsMapped():
    # arrange
    ci_env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REF_NAME": "main",
        "GITHUB_SHA": "abcdef1234567890",  # pragma: allowlist secret
        "GITHUB_RUN_NUMBER": "42",
    }

    # act
    properties = build_environment("https://eds.example", "not live", ci_env, categorized_tests=0)

    # assert
    assert properties["Base.URL"] == "https://eds.example"
    assert properties["Test.Scope"] == "not live"
    assert properties["CI.Branch"] == "main"
    assert properties["CI.Commit"] == "abcdef1"
    assert properties["CI.Run"] == "42"
    assert properties["pytest"] == version("pytest")
    assert properties["requests"] == version("requests")
    assert properties["Python"] == platform.python_version()
    assert properties["OS"] == platform.system()
    for package in TRACKED_PACKAGES:
        assert properties[package] == version(package)
    assert properties["Categories"] == categories_note(0)
    expected_keys = {"Base.URL", "Test.Scope", "Python", "OS", "Categories", "CI.Branch", "CI.Commit", "CI.Run"}
    assert set(properties) == expected_keys | set(TRACKED_PACKAGES)


def test_givenNoMarkerExpressionAndNoCi_whenBuildingEnvironment_thenScopeIsAllAndCiFieldsAreAbsent():
    # act
    properties = build_environment("https://eds.example", "", {}, categorized_tests=0)

    # assert
    assert properties["Test.Scope"] == "all (offline + live)"
    assert not any(key.startswith("CI.") for key in properties)


def test_givenProperties_whenWritingEnvironment_thenFileHasOneKeyValuePerLine(tmp_path):
    # arrange
    properties = {"Base.URL": "https://eds.example", "Python": "3.12.2"}

    # act
    write_environment(str(tmp_path / "results"), properties)

    # assert
    written = (tmp_path / "results" / "environment.properties").read_text(encoding="utf-8")
    assert written.splitlines() == ["Base.URL=https://eds.example", "Python=3.12.2"]


def test_givenFailedErrorAndSkippedReports_whenCountingCategorized_thenAllThreeAreCounted():
    # arrange
    class Reporter:
        stats = {"passed": ["a", "b", "c", "d"], "failed": ["e", "f"], "error": ["g"], "skipped": ["h"], "rerun": ["i"]}

    class PluginManager:
        def get_plugin(self, name):
            return Reporter() if name == "terminalreporter" else None

    class Config:
        pluginmanager = PluginManager()

    class Session:
        config = Config()

    # act
    counted = count_categorized(Session())

    # assert
    assert counted == 4
