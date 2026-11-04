import pytest

from tests.support.allure_labels import labels
from tests.support.mocks import load_mock
from tests.support.schema import assert_all_match_schema

pytestmark = labels("News API", "News")

NEWS_ENDPOINTS = {
    "list": "/News",
    "actual": "/News/actual",
    "calendar": "/News/calendar",
    "archived": "/News/archived",
}


@pytest.mark.parametrize(("method", "expected_path"), NEWS_ENDPOINTS.items())
def test_whenCallingNewsApiMethod_thenRequestGoesToItsEndpointPath(
    eds, news_api, method, expected_path
):
    # arrange
    eds.news(expected_path.removeprefix("/News")).answers(json=[])

    # act
    getattr(news_api, method)()

    # assert
    assert eds.last_request.path == expected_path
    assert eds.last_request.query == {}


@pytest.mark.parametrize(
    ("sample_file", "schema_file", "wrap_in_list"),
    [
        ("news_list_sample.json", "news_schema.json", False),
        ("news_actual_sample.json", "news_schema.json", True),
        ("news_calendar_sample.json", "news_calendar_schema.json", False),
    ],
    ids=["list", "actual", "calendar"],
)
def test_givenNewsSample_whenValidatingAgainstSchema_thenSchemaIsSatisfied(
    sample_file, schema_file, wrap_in_list
):
    # arrange
    sample = load_mock(sample_file)
    items = [sample] if wrap_in_list else sample

    # act / assert
    assert_all_match_schema(items, schema_file)


def test_givenNoCategory_whenGettingActualNews_thenNoCategoryParameterIsSent(eds, news_api):
    # arrange
    eds.news("actual").answers(json=load_mock("news_actual_sample.json"))

    # act
    news_api.actual()

    # assert
    assert eds.last_request.query == {}


def test_givenDate_whenGettingArchivedNews_thenDateIsSent(eds, news_api):
    # arrange
    eds.news("archived").answers(json=[])

    # act
    news_api.archived(date="2026-01-01")

    # assert
    assert eds.last_request.query == {"date": ["2026-01-01"]}
