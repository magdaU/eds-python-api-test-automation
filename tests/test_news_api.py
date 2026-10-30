from urllib.parse import urlparse

import pytest

from tests.support.allure_labels import labels
from tests.support.mocks import load_mock, sent_query
from tests.support.schema import assert_all_match_schema

pytestmark = labels("News API", "News")

NEWS_ENDPOINTS = {"list": "/News", "actual": "/News/actual", "calendar": "/News/calendar", "archived": "/News/archived"}


@pytest.mark.parametrize(("method", "expected_path"), NEWS_ENDPOINTS.items())
def test_whenCallingNewsApiMethod_thenRequestGoesToItsEndpointPath(news_api, requests_mock, method, expected_path):
    # arrange
    requests_mock.get(news_api.url(expected_path.removeprefix("/News")), json=[])

    # act
    getattr(news_api, method)()

    # assert
    assert urlparse(requests_mock.last_request.url).path == expected_path
    assert sent_query(requests_mock) == {}


@pytest.mark.parametrize(
    ("sample_file", "schema_file", "wrap_in_list"),
    [
        ("news_list_sample.json", "news_schema.json", False),
        ("news_actual_sample.json", "news_schema.json", True),
        ("news_calendar_sample.json", "news_calendar_schema.json", False),
    ],
    ids=["list", "actual", "calendar"],
)
def test_givenNewsSample_whenValidatingAgainstSchema_thenSchemaIsSatisfied(sample_file, schema_file, wrap_in_list):
    # arrange
    sample = load_mock(sample_file)
    items = [sample] if wrap_in_list else sample

    # act / assert
    assert_all_match_schema(items, schema_file)


def test_givenNoCategory_whenGettingActualNews_thenNoCategoryParameterIsSent(news_api, requests_mock):
    # arrange
    requests_mock.get(news_api.url("actual"), json=load_mock("news_actual_sample.json"))

    # act
    news_api.actual()

    # assert
    assert sent_query(requests_mock) == {}


def test_givenDate_whenGettingArchivedNews_thenDateIsSent(news_api, requests_mock):
    # arrange
    requests_mock.get(news_api.url("archived"), json=[])

    # act
    news_api.archived(date="2026-01-01")

    # assert
    assert sent_query(requests_mock) == {"date": ["2026-01-01"]}
