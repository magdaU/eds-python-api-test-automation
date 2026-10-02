import json

import allure
import jsonschema
import pytest

BASE_URL = "https://api.energidataservice.dk"
NEWS_URL = f"{BASE_URL}/News"
NEWS_FIELDS = {"newsId", "category", "header", "story", "validFrom", "lastUpdated"}
NEWS_PATHS = ["", "actual", "calendar", "archived"]
SAMPLE_BY_PATH = {
    "": "news_list_sample.json",
    "actual": "news_actual_sample.json",
    "calendar": "news_calendar_sample.json",
    "archived": "news_list_sample.json",
}


def _load_mock(filename):
    with open(f"tests/mocks/{filename}") as f:
        return json.load(f)


def _load_schema(filename):
    with open(f"schemas/{filename}") as f:
        return json.load(f)


def _news_url(path):
    return f"{NEWS_URL}/{path}" if path else NEWS_URL


def _assert_all_match_schema(items, schema_filename):
    schema = _load_schema(schema_filename)
    for item in items:
        jsonschema.validate(instance=item, schema=schema)


@allure.feature("News")
@pytest.mark.parametrize("path", NEWS_PATHS)
def test_whenGettingNewsEndpoint_thenStatusIsOkAndBodyIsJson(eds_client, requests_mock, path):
    # arrange
    requests_mock.get(
        _news_url(path),
        json=_load_mock(SAMPLE_BY_PATH[path]),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )

    # act
    response = eds_client.get_news(path)

    # assert
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    response.json()


@allure.feature("News")
def test_whenGettingNews_thenResponseIsListOfNewsItems(eds_client, requests_mock):
    # arrange
    requests_mock.get(NEWS_URL, json=_load_mock("news_list_sample.json"))

    # act
    body = eds_client.get_news().json()

    # assert
    assert isinstance(body, list)
    assert len(body) == 3
    _assert_all_match_schema(body, "news_schema.json")


@allure.feature("News")
def test_whenGettingNews_thenEveryFieldIsMappedToItsOwnValue(eds_client, requests_mock):
    # arrange
    requests_mock.get(NEWS_URL, json=_load_mock("news_list_sample.json"))

    # act
    first = eds_client.get_news().json()[0]

    # assert
    assert set(first) == NEWS_FIELDS
    assert first["newsId"] == 201
    assert first["category"] == "HIGH"
    assert first["header"] == "Planned maintenance of the data platform"
    assert first["story"] == "The platform will be unavailable on Saturday night during planned maintenance."
    assert first["validFrom"] == "2026-03-30T00:00:00"
    assert first["lastUpdated"] == "2026-03-31T08:15:00"


@allure.feature("News")
def test_givenNewsList_whenCheckingCategories_thenOnlyKnownCategoriesAppear(eds_client, requests_mock):
    # arrange
    requests_mock.get(NEWS_URL, json=_load_mock("news_list_sample.json"))

    # act
    categories = {item["category"] for item in eds_client.get_news().json()}

    # assert
    assert categories == {"HIGH", "INFO"}


@allure.feature("News")
@pytest.mark.parametrize("query", [{"limit": 1}, {"sort": "newsId desc"}])
def test_givenUnsupportedParameter_whenGettingNews_thenParameterIsSentAndListIsUnchanged(
        eds_client, requests_mock, query):
    # arrange
    requests_mock.get(NEWS_URL, json=_load_mock("news_list_sample.json"))

    # act
    response = eds_client.get_news(params=query)

    # assert
    key, value = next(iter(query.items()))
    assert requests_mock.last_request.qs[key] == [str(value).lower()]
    assert len(response.json()) == 3


@allure.feature("News")
@pytest.mark.parametrize("category", ["HIGH", "INFO"])
def test_givenCategory_whenGettingActualNews_thenSingleNewsObjectIsReturned(eds_client, requests_mock, category):
    # arrange
    requests_mock.get(_news_url("actual"), json=_load_mock("news_actual_sample.json"))

    # act
    response = eds_client.get_news("actual", {"category": category})

    # assert
    body = response.json()
    assert requests_mock.last_request.qs["category"] == [category.lower()]
    assert isinstance(body, dict)
    assert set(body) == NEWS_FIELDS
    _assert_all_match_schema([body], "news_schema.json")


@allure.feature("News")
def test_whenGettingActualNewsWithoutCategory_thenBadRequestNamesMissingField(eds_client, requests_mock):
    # arrange
    requests_mock.get(
        _news_url("actual"),
        status_code=400,
        json={"title": "One or more validation errors occurred.", "status": 400,
              "errors": {"category": ["The category field is required."]}},
        headers={"Content-Type": "application/problem+json; charset=utf-8"},
    )

    # act
    response = eds_client.get_news("actual")

    # assert
    assert response.status_code == 400
    assert "category" in response.json()["errors"]


@allure.feature("News")
def test_givenNoActualNewsForCategory_whenGettingActualNews_thenNoContentIsReturned(eds_client, requests_mock):
    # arrange
    requests_mock.get(_news_url("actual"), status_code=204)

    # act
    response = eds_client.get_news("actual", {"category": "LOW"})

    # assert
    assert response.status_code == 204
    assert response.content == b""


@allure.feature("News")
def test_whenGettingCalendar_thenEachEntryHasYearAndStoryCount(eds_client, requests_mock):
    # arrange
    requests_mock.get(_news_url("calendar"), json=_load_mock("news_calendar_sample.json"))

    # act
    body = eds_client.get_news("calendar").json()

    # assert
    assert isinstance(body, list)
    _assert_all_match_schema(body, "news_calendar_schema.json")
    assert [(e["dateString"], e["numberOfNewsStories"]) for e in body] == [("2026", 3), ("2025", 2), ("2024", 5)]


@allure.feature("News")
def test_givenDate_whenGettingArchivedNews_thenNewsListIsReturned(eds_client, requests_mock):
    # arrange
    requests_mock.get(_news_url("archived"), json=_load_mock("news_list_sample.json"))

    # act
    response = eds_client.get_news("archived", {"date": "2026-01-01"})

    # assert
    body = response.json()
    assert requests_mock.last_request.qs["date"] == ["2026-01-01"]
    assert isinstance(body, list)
    _assert_all_match_schema(body, "news_schema.json")


@allure.feature("News")
def test_givenNoDate_whenGettingArchivedNews_thenArchiveIsEmpty(eds_client, requests_mock):
    # arrange
    requests_mock.get(_news_url("archived"), json=[])

    # act
    response = eds_client.get_news("archived")

    # assert
    assert response.status_code == 200
    assert response.json() == []


@allure.feature("News")
def test_givenInvalidDate_whenGettingArchivedNews_thenBadRequestNamesDateField(eds_client, requests_mock):
    # arrange
    requests_mock.get(
        _news_url("archived"),
        status_code=400,
        json={"title": "One or more validation errors occurred.", "status": 400,
              "errors": {"date": ["The value 'bogus' is not valid."]}},
        headers={"Content-Type": "application/problem+json; charset=utf-8"},
    )

    # act
    response = eds_client.get_news("archived", {"date": "bogus"})

    # assert
    assert response.status_code == 400
    assert "date" in response.json()["errors"]


@allure.feature("News")
@pytest.mark.parametrize("path", ["", "calendar"])
def test_givenServerError_whenGettingNews_thenStatusIsPassedThrough(eds_client, requests_mock, path):
    # arrange
    requests_mock.get(_news_url(path), status_code=500)

    # act
    response = eds_client.get_news(path)

    # assert
    assert response.status_code == 500


@allure.feature("News")
def test_whenGettingLiveNews_thenEveryItemMatchesSchema(eds_client):
    # act
    response = eds_client.get_news()

    # assert
    assert response.status_code == 200
    _assert_all_match_schema(response.json(), "news_schema.json")


@allure.feature("News")
def test_whenGettingLiveCalendar_thenEveryEntryMatchesSchemaAndArchiveAgrees(eds_client):
    # arrange
    calendar = eds_client.get_news("calendar").json()
    latest = calendar[0]

    # act
    archived = eds_client.get_news("archived", {"date": f"{latest['dateString']}-01-01"}).json()

    # assert
    _assert_all_match_schema(calendar, "news_calendar_schema.json")
    assert len(archived) == latest["numberOfNewsStories"]
    assert all(item["validFrom"].startswith(latest["dateString"]) for item in archived)
