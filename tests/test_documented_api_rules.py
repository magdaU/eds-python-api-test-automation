"""Rules stated on the EDS API guide (https://www.energidataservice.dk/guides/api-guides), checked
against the requests the client builds. Offline: the API is mocked, nothing is sent to it."""

import json

import pytest

from tests.support.allure_labels import labels

pytestmark = labels("Dataset API", "Documented rules", "critical")


@pytest.mark.xfail(
    strict=True,
    reason="the guide says a single quote in a filter value is written as two quotes; "
    "the client does not do this yet (know-how/TODO.md, section 7, item A)",
)
def test_givenFilterValueWithSingleQuote_whenGettingDataset_thenTheQuoteIsDoubled(
    eds, dataset, dataset_api
):
    # arrange
    eds.dataset(dataset.name).answers()

    # act
    dataset_api.get(filters={"PriceArea": ["O'Brien"]})

    # assert
    sent = json.loads(eds.last_request.query["filter"][0])
    assert sent == {"PriceArea": ["O''Brien"]}
