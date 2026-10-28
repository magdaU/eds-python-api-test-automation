from tests.support.allure_labels import labels
from tests.support.mocks import load_mock
from tests.support.schema import assert_matches_schema

pytestmark = labels("Test support", "Fixture paths")


def test_givenOtherWorkingDirectory_whenLoadingMock_thenFileIsFound(tmp_path, monkeypatch):
    # arrange
    monkeypatch.chdir(tmp_path)

    # act
    body = load_mock("co2emis_sample.json")

    # assert
    assert body["records"]


def test_givenOtherWorkingDirectory_whenValidatingAgainstSchema_thenSchemaIsFound(tmp_path, monkeypatch):
    # arrange
    monkeypatch.chdir(tmp_path)
    body = {"records": [], "total": 0}

    # act / assert
    assert_matches_schema(body, "co2emis_schema.json")
