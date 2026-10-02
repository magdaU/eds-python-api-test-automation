from tests.support.mocks import load_mock, records_response


def test_givenConsecutiveOffsets_whenGettingPages_thenPagesDoNotOverlap(co2_api, requests_mock):
    # arrange
    requests_mock.get(co2_api.url, [
        {"json": load_mock("co2_page1.json")},
        {"json": load_mock("co2_page2.json")},
    ])

    # act
    first_page = co2_api.get(limit=5, offset=0).json()
    second_page = co2_api.get(limit=5, offset=5).json()

    # assert
    first_timestamps = {record["Minutes5UTC"] for record in first_page["records"]}
    second_timestamps = {record["Minutes5UTC"] for record in second_page["records"]}
    assert len(first_page["records"]) == 5
    assert len(second_page["records"]) == 5
    assert first_timestamps.isdisjoint(second_timestamps)


def test_givenOffset_whenGettingDataset_thenOffsetParameterIsSent(co2_api, requests_mock):
    # arrange
    requests_mock.get(co2_api.url, json=records_response([]))

    # act
    co2_api.get(limit=5, offset=10)

    # assert
    assert requests_mock.last_request.qs["offset"] == ["10"]


def test_givenLimitZero_whenGettingDataset_thenAllRecordsAreReturned(co2_api, requests_mock):
    # arrange
    all_records = load_mock("co2_page1.json")["records"] + load_mock("co2_page2.json")["records"]
    requests_mock.get(co2_api.url, json=records_response(all_records))

    # act
    response = co2_api.get(limit=0)

    # assert
    assert len(response.json()["records"]) == len(all_records)
