from tests.support.mocks import load_mock, records_response


def test_givenAscendingSort_whenGettingDataset_thenPricesAreAscending(elspotprices_api, requests_mock):
    # arrange
    requests_mock.get(elspotprices_api.url, json=load_mock("elspotprices_sorted.json"))

    # act
    response = elspotprices_api.get(sort="SpotPriceDKK")

    # assert
    prices = [record["SpotPriceDKK"] for record in response.json()["records"]]
    assert prices == sorted(prices)


def test_givenDescendingSort_whenGettingDataset_thenPricesAreDescending(elspotprices_api, requests_mock):
    # arrange
    ascending_records = load_mock("elspotprices_sorted.json")["records"]
    requests_mock.get(elspotprices_api.url, json=records_response(list(reversed(ascending_records))))

    # act
    response = elspotprices_api.get(sort="SpotPriceDKK desc")

    # assert
    prices = [record["SpotPriceDKK"] for record in response.json()["records"]]
    assert prices == sorted(prices, reverse=True)


def test_givenSort_whenGettingDataset_thenSortParameterIsSent(elspotprices_api, requests_mock):
    # arrange
    requests_mock.get(elspotprices_api.url, json=records_response([]))

    # act
    elspotprices_api.get(sort="SpotPriceDKK desc")

    # assert
    assert requests_mock.last_request.qs["sort"] == ["spotpricedkk desc"]
