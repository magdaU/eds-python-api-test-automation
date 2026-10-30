"""Property-based tests (hypothesis): invariants that must hold for any input, not just chosen examples."""

import json
from urllib.parse import parse_qs, urlparse

import pytest
import requests_mock
from hypothesis import given, settings
from hypothesis import strategies as st

from client.eds_client import EDSApiClient
from tests.support.allure_labels import labels

pytestmark = labels("Client library", "Property-based")

BASE = "http://localhost:9999"

non_negative_ints = st.integers(min_value=0, max_value=10**9)
json_scalars = st.one_of(st.text(), st.integers(), st.booleans(), st.none())
filter_dicts = st.dictionaries(st.text(min_size=1), st.one_of(json_scalars, st.lists(json_scalars)))

settings.register_profile("default", max_examples=100, deadline=None)
settings.load_profile("default")


def get_sent_query(**arguments):
    client = EDSApiClient(base_url=BASE)
    with requests_mock.Mocker() as mocker:
        mocker.get(client.dataset_url("CO2Emis"), json={"records": [], "total": 0})
        client.get_dataset("CO2Emis", **arguments)
        return parse_qs(urlparse(mocker.last_request.url).query)


@given(limit=non_negative_ints, offset=non_negative_ints, sort=st.text(min_size=1), filters=filter_dicts)
def test_givenAnyValidParameters_whenGettingDataset_thenEveryParameterSurvivesTheUrl(limit, offset, sort, filters):
    # act
    query = get_sent_query(limit=limit, offset=offset, sort=sort, filters=filters)

    # assert
    assert query["limit"] == [str(limit)]
    assert query["offset"] == [str(offset)]
    assert query["sort"] == [sort]
    assert json.loads(query["filter"][0]) == filters


@given(limit=st.integers(max_value=-1))
def test_givenAnyNegativeLimit_whenGettingDataset_thenValueErrorIsRaisedBeforeSending(limit):
    # arrange
    client = EDSApiClient(base_url=BASE)

    # act / assert
    with requests_mock.Mocker() as mocker:
        with pytest.raises(ValueError, match="limit"):
            client.get_dataset("CO2Emis", limit=limit)
        assert mocker.call_count == 0


@given(
    path=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), max_size=20), padding=st.sampled_from(["", "/"])
)
def test_givenAnyPathWithOptionalSlashes_whenBuildingNewsUrl_thenThereIsNoDoubleSlash(path, padding):
    # arrange
    client = EDSApiClient(base_url=BASE + padding)

    # act
    url = client.news_url(padding + path + padding)

    # assert
    assert "//" not in url.removeprefix("http://")
    assert url.startswith(f"{BASE}/News")
