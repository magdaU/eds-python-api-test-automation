import pytest

DATASET = "Elspotprices"


def test_status_code_ok(elspotprices_response):
    assert elspotprices_response.status_code == 200


def test_response_is_json(elspotprices_response):
    assert elspotprices_response.headers["Content-Type"].startswith("application/json")
    elspotprices_response.json()


def test_response_structure(elspotprices_response):
    body = elspotprices_response.json()

    assert "records" in body
    assert "total" in body
    assert isinstance(body["records"], list)


@pytest.mark.parametrize("limit", [1, 3, 5, 10])
def test_limit_parameter_returns_expected_number_of_records(eds_client, limit):
    response = eds_client.get_dataset(DATASET, limit=limit)
    body = response.json()

    assert response.status_code == 200
    assert len(body["records"]) == limit


@pytest.mark.parametrize("price_area", ["DK1", "DK2"])
def test_filter_parameter_returns_matching_records(eds_client, price_area):
    response = eds_client.get_dataset(DATASET, limit=5, filter={"PriceArea": price_area})
    body = response.json()

    assert response.status_code == 200
    assert all(record["PriceArea"] == price_area for record in body["records"])

def test_sort_descending_returns_ordered_records(eds_client):
        response = eds_client.get_dataset(DATASET, limit=5, sort="SpotPriceDKK desc")
        prices = [r["SpotPriceDKK"] for r in response.json()["records"]]

        assert prices == sorted(prices, reverse=True)
