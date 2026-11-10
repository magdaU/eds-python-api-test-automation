"""Property-based tests (hypothesis): invariants that must hold for any input, not just chosen
examples."""

import json

import requests_mock
from hypothesis import given
from hypothesis import strategies as st

from client.eds_client import EDSApiClient
from tests.support.allure_labels import labels
from tests.support.fake_eds import FakeEds

pytestmark = labels("Client library", "Property-based")

BASE = "http://localhost:9999"

non_negative_ints = st.integers(min_value=0, max_value=10**9)
json_scalars = st.one_of(st.text(), st.integers(), st.booleans(), st.none())
filter_dicts = st.dictionaries(st.text(min_size=1), st.one_of(json_scalars, st.lists(json_scalars)))


def get_sent_query(**arguments):
    client = EDSApiClient(base_url=BASE)
    with requests_mock.Mocker() as mocker:
        eds = FakeEds(mocker, client)
        eds.dataset("CO2Emis").answers()
        client.get_dataset("CO2Emis", **arguments)
        return eds.last_request.query


@given(
    limit=non_negative_ints,
    offset=non_negative_ints,
    sort=st.text(min_size=1),
    filters=filter_dicts,
)
def test_givenAnyValidParameters_whenGettingDataset_thenEveryParameterSurvivesTheUrl(
    limit, offset, sort, filters
):
    # act
    query = get_sent_query(limit=limit, offset=offset, sort=sort, filters=filters)

    # assert
    assert query["limit"] == [str(limit)]
    assert query["offset"] == [str(offset)]
    assert query["sort"] == [sort]
    assert json.loads(query["filter"][0]) == filters
