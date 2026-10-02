import allure
import pytest

from tests.support.mocks import load_mock
from tests.support.schema import assert_all_match_schema

NEWS_ITEM_FIELDS = {"newsId", "category", "header", "story", "validFrom", "lastUpdated"}
NEWS_ENDPOINT_PATHS = ["", "actual", "calendar", "archived"]
NEWS_SAMPLE_BY_PATH = {
    "": "news_list_sample.json",
    "actual": "news_actual_sample.json",
    "calendar": "news_calendar_sample.json",
    "archived": "news_list_sample.json",
}
VALIDATION_PROBLEM_JSON = {"Content-Type": "application/problem+json; charset=utf-8"}


@pytest.fixture(autouse=True)
def allure_feature_news():
    allure.dynamic.feature("News")


@pytest.mark.parametrize("path", NEWS_ENDPOINT_PATHS)
def test_whenGettingNewsEndpoint_thenStatusIsOkAndBodyIsJson(news_api, requests_mock, path):
    # arrange
    requests_mock.get(
        news_api.url(path),
        json=load_mock(NEWS_SAMPLE_BY_PATH[path]),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

    # act
    response = news_api.get(path)

    # assert
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    response.json()


def test_whenGettingNews_thenResponseIsListOfNewsItems(news_api, requests_mock):
    # arrange
    requests_mock.get(news_api.url(), json=load_mock("news_list_sample.json"))

    # act
    body = news_api.list().json()

    # assert
    assert isinstance(body, list)
    assert len(body) == 3
    assert_all_match_schema(body, "news_schema.json")


def test_whenGettingNews_thenEveryFieldIsMappedToItsOwnValue(news_api, requests_mock):
    # arrange
    requests_mock.get(news_api.url(), json=load_mock("news_list_sample.json"))

    # act
    first = news_api.list().json()[0]

    # assert
    assert set(first) == NEWS_ITEM_FIELDS
    assert first["newsId"] == 201
    assert first["category"] == "HIGH"
    assert first["header"] == "Planned maintenance of the data platform"
    assert first["story"] == "The platform will be unavailable on Saturday night during planned maintenance."
    assert first["validFrom"] == "2026-03-30T00:00:00"
    assert first["lastUpdated"] == "2026-03-31T08:15:00"


def test_givenNewsList_whenCheckingCategories_thenOnlyKnownCategoriesAppear(news_api, requests_mock):
    # arrange
    requests_mock.get(news_api.url(), json=load_mock("news_list_sample.json"))

    # act
    categories = {item["category"] for item in news_api.list().json()}

    # assert
    assert categories == {"HIGH", "INFO"}


@pytest.mark.parametrize("query", [{"limit": 1}, {"sort": "newsId desc"}])
def test_givenUnsupportedParameter_whenGettingNews_thenParameterIsSentAndListIsUnchanged(
        news_api, requests_mock, query):
    # arrange
    requests_mock.get(news_api.url(), json=load_mock("news_list_sample.json"))

    # act
    response = news_api.get(params=query)

    # assert
    key, value = next(iter(query.items()))
    assert requests_mock.last_request.qs[key] == [str(value).lower()]
    assert len(response.json()) == 3


@pytest.mark.parametrize("category", ["HIGH", "INFO"])
def test_givenCategory_whenGettingActualNews_thenSingleNewsObjectIsReturned(news_api, requests_mock, category):
    # arrange
    requests_mock.get(news_api.url("actual"), json=load_mock("news_actual_sample.json"))

    # act
    body = news_api.actual(category).json()

    # assert
    assert requests_mock.last_request.qs["category"] == [category.lower()]
    assert isinstance(body, dict)
    assert set(body) == NEWS_ITEM_FIELDS
    assert_all_match_schema([body], "news_schema.json")


def test_whenGettingActualNewsWithoutCategory_thenBadRequestNamesMissingField(news_api, requests_mock):
    # arrange
    requests_mock.get(
        news_api.url("actual"),
        status_code=400,
        json={"title": "One or more validation errors occurred.", "status": 400,
              "errors": {"category": ["The category field is required."]}},
        headers=VALIDATION_PROBLEM_JSON,
    )

    # act
    response = news_api.actual()

    # assert
    assert response.status_code == 400
    assert "category" in response.json()["errors"]


def test_givenNoActualNewsForCategory_whenGettingActualNews_thenNoContentIsReturned(news_api, requests_mock):
    # arrange
    requests_mock.get(news_api.url("actual"), status_code=204)

    # act
    response = news_api.actual("LOW")

    # assert
    assert response.status_code == 204
    assert response.content == b""


def test_whenGettingCalendar_thenEachEntryHasYearAndStoryCount(news_api, requests_mock):
    # arrange
    requests_mock.get(news_api.url("calendar"), json=load_mock("news_calendar_sample.json"))

    # act
    body = news_api.calendar().json()

    # assert
    assert isinstance(body, list)
    assert_all_match_schema(body, "news_calendar_schema.json")
    assert [(entry["dateString"], entry["numberOfNewsStories"]) for entry in body] == [
        ("2026", 3), ("2025", 2), ("2024", 5)]


def test_givenDate_whenGettingArchivedNews_thenNewsListIsReturned(news_api, requests_mock):
    # arrange
    requests_mock.get(news_api.url("archived"), json=load_mock("news_list_sample.json"))

    # act
    body = news_api.archived(date="2026-01-01").json()

    # assert
    assert requests_mock.last_request.qs["date"] == ["2026-01-01"]
    assert isinstance(body, list)
    assert_all_match_schema(body, "news_schema.json")


def test_givenNoDate_whenGettingArchivedNews_thenArchiveIsEmpty(news_api, requests_mock):
    # arrange
    requests_mock.get(news_api.url("archived"), json=[])

    # act
    response = news_api.archived()

    # assert
    assert response.status_code == 200
    assert response.json() == []


def test_givenInvalidDate_whenGettingArchivedNews_thenBadRequestNamesDateField(news_api, requests_mock):
    # arrange
    requests_mock.get(
        news_api.url("archived"),
        status_code=400,
        json={"title": "One or more validation errors occurred.", "status": 400,
              "errors": {"date": ["The value 'bogus' is not valid."]}},
        headers=VALIDATION_PROBLEM_JSON,
    )

    # act
    response = news_api.archived(date="bogus")

    # assert
    assert response.status_code == 400
    assert "date" in response.json()["errors"]


@pytest.mark.parametrize("path", ["", "calendar"])
def test_givenServerError_whenGettingNews_thenStatusIsPassedThrough(news_api, requests_mock, path):
    # arrange
    requests_mock.get(news_api.url(path), status_code=500)

    # act
    response = news_api.get(path)

    # assert
    assert response.status_code == 500
