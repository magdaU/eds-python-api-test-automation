import datetime as dt
from dataclasses import dataclass

import pytest

from tests.support.data_quality import DataQualityError, utc_time


@dataclass(frozen=True)
class FakeSeries:
    """The part of a live series definition that `utc_time` reads."""

    dataset: str
    time_field: str


SERIES = FakeSeries("CO2Emis", "Minutes5UTC")


def test_givenUtcTimestampWithZSuffix_whenConverting_thenSameInstantInUtc():
    # arrange
    record = {"Minutes5UTC": "2026-11-05T09:05:00Z"}

    # act
    result = utc_time(record, SERIES)

    # assert
    assert result == dt.datetime(2026, 11, 5, 9, 5, tzinfo=dt.UTC)
    assert result.tzinfo == dt.UTC


def test_givenTimestampWithPlusOneOffset_whenConverting_thenHourShiftsBackToUtc():
    # arrange
    record = {"Minutes5UTC": "2026-11-05T10:05:00+01:00"}

    # act
    result = utc_time(record, SERIES)

    # assert
    assert result == dt.datetime(2026, 11, 5, 9, 5, tzinfo=dt.UTC)
    assert result.hour == 9
    assert result.utcoffset() == dt.timedelta(0)


def test_givenTimestampWithMinusFiveOffset_whenConverting_thenHourShiftsForwardToUtc():
    # arrange
    record = {"Minutes5UTC": "2026-11-05T04:30:00-05:00"}

    # act
    result = utc_time(record, SERIES)

    # assert
    assert result == dt.datetime(2026, 11, 5, 9, 30, tzinfo=dt.UTC)
    assert result.hour == 9
    assert result.minute == 30


def test_givenNaiveTimestamp_whenConverting_thenTreatedAsUtcByDocumentedRule():
    # arrange
    record = {"Minutes5UTC": "2026-11-05T09:05:00"}

    # act
    result = utc_time(record, SERIES)

    # assert
    assert result == dt.datetime(2026, 11, 5, 9, 5, tzinfo=dt.UTC)
    assert result.hour == 9
    assert result.tzinfo == dt.UTC


def test_givenMissingField_whenConverting_thenDataQualityErrorNamesFieldAndDataset():
    # arrange
    record = {"TimeDK": "2026-11-05T10:05:00"}

    # act
    with pytest.raises(DataQualityError) as error:
        utc_time(record, SERIES)

    # assert
    assert "Minutes5UTC" in str(error.value)
    assert "CO2Emis" in str(error.value)


def test_givenNoneValue_whenConverting_thenDataQualityErrorNamesFieldAndDataset():
    # arrange
    record = {"Minutes5UTC": None}

    # act
    with pytest.raises(DataQualityError) as error:
        utc_time(record, SERIES)

    # assert
    assert "Minutes5UTC" in str(error.value)
    assert "CO2Emis" in str(error.value)
    assert "None" in str(error.value)


def test_givenInvalidDateFormat_whenConverting_thenDataQualityErrorQuotesTheValue():
    # arrange
    record = {"Minutes5UTC": "05.11.2026 09:05"}

    # act
    with pytest.raises(DataQualityError) as error:
        utc_time(record, SERIES)

    # assert
    assert "Minutes5UTC" in str(error.value)
    assert "ISO 8601" in str(error.value)
    assert "05.11.2026 09:05" in str(error.value)


def test_givenNonStringValue_whenConverting_thenDataQualityErrorNamesTheType():
    # arrange
    record = {"Minutes5UTC": 1793869500}

    # act
    with pytest.raises(DataQualityError) as error:
        utc_time(record, SERIES)

    # assert
    assert "Minutes5UTC" in str(error.value)
    assert "CO2Emis" in str(error.value)
    assert "int" in str(error.value)
