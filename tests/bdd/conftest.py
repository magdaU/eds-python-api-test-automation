"""Step definitions shared by the Gherkin scenarios in `features/`.

Steps reuse the project's API objects, `requests-mock` and the scripted local HTTP server, so a scenario reads as a
specification while the checks run through the same code as the other tests.
"""

from dataclasses import dataclass, field
from typing import Any

import pytest
import requests
from pytest_bdd import given, parsers, then, when

from client.dataset_api import DatasetApi
from client.retry import RetryAfterTooLongError
from tests.support.mocks import load_mock, records_response, sent_query
from tests.support.scripted_server import api_for


@dataclass
class World:
    """What a scenario has set up and observed so far."""

    api: Any = None
    server: Any = None
    response: requests.Response | None = None
    error: Exception | None = None
    waits: list[float] = field(default_factory=list)


@pytest.fixture
def world():
    return World()


def attempt(world, request):
    """Run a request and keep either its response or the exception it raised."""
    try:
        world.response = request()
    except (ValueError, requests.exceptions.RequestException) as error:
        world.error = error


# --- datasets (mocked HTTP) ---


@given(parsers.parse("the {dataset} dataset answers with an empty result"))
def dataset_answers_empty(world, eds_client, requests_mock, dataset):
    world.api = DatasetApi(eds_client, dataset)
    requests_mock.get(world.api.url, json=records_response([]))


@when(parsers.parse("I get the dataset with limit {limit:d} and offset {offset:d}"))
def get_with_limit_and_offset(world, limit, offset):
    attempt(world, lambda: world.api.get(limit=limit, offset=offset))


@when(parsers.parse("I get the dataset with limit {limit:d}"))
def get_with_limit(world, limit):
    attempt(world, lambda: world.api.get(limit=limit))


@when(parsers.parse('I get the dataset sorted by "{sort}"'))
def get_sorted(world, sort):
    attempt(world, lambda: world.api.get(sort=sort))


@when(parsers.parse('I get the dataset filtered by price area "{area}"'))
def get_filtered(world, area):
    attempt(world, lambda: world.api.get(filters={"PriceArea": area}))


@then(parsers.parse('the request carries limit "{limit}" and offset "{offset}"'))
def request_has_limit_and_offset(requests_mock, limit, offset):
    assert sent_query(requests_mock) == {"limit": [limit], "offset": [offset]}


@then(parsers.parse('the request carries sort "{sort}"'))
def request_has_sort(requests_mock, sort):
    assert sent_query(requests_mock) == {"sort": [sort]}


@then(parsers.parse("the request carries the filter '{filter_json}'"))
def request_has_filter(requests_mock, filter_json):
    assert sent_query(requests_mock) == {"filter": [filter_json]}


@then("the client refuses the request and names the limit")
def client_refuses_naming_limit(world):
    assert isinstance(world.error, ValueError)
    assert "limit" in str(world.error)


@then("no request was sent")
def no_request_sent(requests_mock):
    assert requests_mock.call_count == 0


# --- resilience (scripted local HTTP server) ---


@given(parsers.parse('an API that answers {first:d} with "Retry-After: {seconds:d}" and then {last:d}'))
def api_throttles_once(world, scripted_server, monkeypatch, first, seconds, last):
    world.server = scripted_server(first, last, headers={"Retry-After": str(seconds)})
    monkeypatch.setattr("urllib3.util.retry.time.sleep", world.waits.append)


@given(parsers.parse("an API that always answers {status:d}"))
def api_always_answers(world, scripted_server, monkeypatch, status):
    world.server = scripted_server(status)
    monkeypatch.setattr("urllib3.util.retry.time.sleep", world.waits.append)


@when("I get a dataset")
def get_a_dataset(world):
    attempt(world, lambda: api_for(world.server, max_retries=2).get())


@then(parsers.parse("the client waited {seconds:d} seconds before it retried"))
def client_waited(world, seconds):
    assert world.waits == [seconds]


@then("the request fails because the server asked for a longer wait than allowed")
def fails_because_wait_too_long(world):
    assert isinstance(world.error, RetryAfterTooLongError)


@then("the client did not wait")
def client_did_not_wait(world):
    assert world.waits == []


@then(parsers.parse("the response status is {status:d}"))
def response_status_is(world, status):
    assert world.error is None
    assert world.response.status_code == status


@then(parsers.parse("the request fails with a retry error after {attempts:d} attempts"))
def fails_with_retry_error(world, attempts):
    assert isinstance(world.error, requests.exceptions.RetryError)
    assert world.server.request_count == attempts


@then(parsers.parse("the API received {count:d} request"))
def api_received_requests(world, count):
    assert world.server.request_count == count


# --- news (mocked HTTP) ---


@given("the news API answers with an actual item")
def news_answers_actual(world, news_api, requests_mock):
    world.api = news_api
    requests_mock.get(news_api.url("actual"), json=load_mock("news_actual_sample.json"))


@given("the news API answers with an empty archive")
def news_answers_empty_archive(world, news_api, requests_mock):
    world.api = news_api
    requests_mock.get(news_api.url("archived"), json=[])


@when(parsers.parse('I ask for the actual news of category "{category}"'))
def ask_actual_news(world, category):
    attempt(world, lambda: world.api.actual(category))


@when("I ask for the archived news without a date")
def ask_archive_without_date(world):
    attempt(world, lambda: world.api.archived())


@then(parsers.parse('the request carries only category "{category}"'))
def request_has_only_category(requests_mock, category):
    assert sent_query(requests_mock) == {"category": [category]}


@then("the request carries no parameters")
def request_has_no_parameters(requests_mock):
    assert sent_query(requests_mock) == {}
