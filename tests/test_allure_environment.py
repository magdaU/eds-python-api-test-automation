import platform
from importlib.metadata import version

from tests.support.allure_environment import TRACKED_PACKAGES, build_environment, write_environment
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "Allure environment")


def test_givenCiEnvironment_whenBuildingEnvironment_thenEveryFieldIsMapped():
    # arrange
    ci_env = {
        "GITHUB_ACTIONS": "true",
        "GITHUB_REF_NAME": "main",
        "GITHUB_SHA": "abcdef1234567890",
        "GITHUB_RUN_NUMBER": "42",
    }

    # act
    properties = build_environment("https://eds.example", "not live", ci_env)

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
    assert set(properties) == {"Base.URL", "Test.Scope", "Python", "OS", "CI.Branch", "CI.Commit", "CI.Run", *TRACKED_PACKAGES}


def test_givenNoMarkerExpressionAndNoCi_whenBuildingEnvironment_thenScopeIsAllAndCiFieldsAreAbsent():
    # act
    properties = build_environment("https://eds.example", "", {})

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
