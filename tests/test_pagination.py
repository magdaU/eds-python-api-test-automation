from tests.support.allure_labels import labels
from tests.support.mocks import records_response

pytestmark = labels("Dataset API", "Pagination")


def test_givenConsecutivePages_whenGettingThem_thenEachRequestAdvancesTheOffsetByTheLimit(co2_api, requests_mock):
    # arrange
    requests_mock.get(co2_api.url, json=records_response([]))
    limit = 5

    # act
    for page in range(3):
        co2_api.get(limit=limit, offset=page * limit)

    # assert
    sent = [(request.qs["limit"], request.qs["offset"]) for request in requests_mock.request_history]
    assert sent == [(["5"], ["0"]), (["5"], ["5"]), (["5"], ["10"])]
