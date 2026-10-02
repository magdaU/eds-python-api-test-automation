import allure
import pytest

from tests.support.mocks import load_mock, records_response


@pytest.fixture(autouse=True)
def allure_feature_for_dataset(dataset):
    allure.dynamic.feature(dataset.name)


def test_whenGettingDataset_thenStatusIsOk(dataset, dataset_api, requests_mock):
    # arrange
    requests_mock.get(dataset_api.url, json=load_mock(dataset.sample_response_file))

    # act
    response = dataset_api.get()

    # assert
    assert response.status_code == 200


def test_whenGettingDataset_thenBodyIsJson(dataset, dataset_api, requests_mock):
    # arrange
    requests_mock.get(
        dataset_api.url,
        json=load_mock(dataset.sample_response_file),
        headers={"Content-Type": "application/json"},
    )

    # act
    response = dataset_api.get()

    # assert
    assert response.headers["Content-Type"].startswith("application/json")
    response.json()


def test_whenGettingDataset_thenResponseHasRecordsAndTotal(dataset, dataset_api, requests_mock):
    # arrange
    requests_mock.get(dataset_api.url, json=load_mock(dataset.sample_response_file))

    # act
    body = dataset_api.get().json()

    # assert
    assert "records" in body
    assert "total" in body
    assert isinstance(body["records"], list)


@pytest.mark.parametrize("limit", [1, 3, 5, 10])
def test_givenLimit_whenGettingDataset_thenReturnsThatManyRecords(dataset, dataset_api, requests_mock, limit):
    # arrange
    all_records = load_mock(dataset.sample_response_file)["records"]
    requests_mock.get(dataset_api.url, json=records_response(all_records[:limit]))

    # act
    response = dataset_api.get(limit=limit)

    # assert
    assert response.status_code == 200
    assert len(response.json()["records"]) == limit


@pytest.mark.parametrize("price_area", ["DK1", "DK2"])
def test_givenPriceArea_whenFilteringDataset_thenOnlyMatchingRecordsAreReturned(
        dataset, dataset_api, requests_mock, price_area):
    # arrange
    all_records = load_mock(dataset.sample_response_file)["records"]
    matching = [record for record in all_records if record["PriceArea"] == price_area]
    requests_mock.get(dataset_api.url, json=records_response(matching))

    # act
    response = dataset_api.get(limit=5, filter={"PriceArea": price_area})

    # assert
    assert response.status_code == 200
    assert all(record["PriceArea"] == price_area for record in response.json()["records"])
