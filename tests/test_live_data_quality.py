"""Data-quality checks on the newest records of the real EDS API, for the nightly run.

Each series is queried once (the 100 newest records) and shared by all checks. The checks do not compare values with an
authoritative source; they catch data that stopped arriving, has holes, is out of range or is labelled with the wrong time.
"""

import datetime as dt
import math
from collections import defaultdict
from dataclasses import dataclass
from itertools import pairwise
from zoneinfo import ZoneInfo

import pytest
from pydantic import BaseModel

import allure
from client.dataset_api import DatasetApi
from client.parsers import parse_records
from models.co2emis import CO2EmisRecord
from models.dayaheadprices import DayAheadPricesRecord
from tests.support.live import TRANSIENT_NETWORK_ERRORS

pytestmark = [
    pytest.mark.live,
    pytest.mark.data_quality,
    allure.epic("Data quality"),
    pytest.mark.flaky(reruns=1, reruns_delay=5, only_rerun=TRANSIENT_NETWORK_ERRORS),
]

COPENHAGEN = ZoneInfo("Europe/Copenhagen")
RECENT_RECORDS = 100
REQUIRED_AREAS = {"DK1", "DK2"}


@dataclass(frozen=True)
class Series:
    dataset: str
    time_field: str  # UTC timestamp of the record
    local_time_field: str  # the same moment in Danish time
    step: dt.timedelta
    max_lag: dt.timedelta  # how far behind the present the newest record may be
    value_field: str
    value_range: tuple[float, float]
    model: type[BaseModel]


# Emissions in g/kWh: 0 to 1000 is far wider than anything observed (39 to 139), so only corrupt values fall outside it.
CO2EMIS = Series(
    "CO2Emis",
    "Minutes5UTC",
    "Minutes5DK",
    dt.timedelta(minutes=5),
    dt.timedelta(hours=2),
    "CO2Emission",
    (0, 1000),
    CO2EmisRecord,
)
# Day-ahead prices are published for the next day, so the newest record lies in the future (lag 0). The market limits are
# about -500 to 4000 EUR/MWh; the bounds are wider on purpose, to catch corrupt values and not market events.
DAYAHEADPRICES = Series(
    "DayAheadPrices",
    "TimeUTC",
    "TimeDK",
    dt.timedelta(minutes=15),
    dt.timedelta(0),
    "DayAheadPriceEUR",
    (-1000, 10000),
    DayAheadPricesRecord,
)


@pytest.fixture(scope="module", params=[CO2EMIS, DAYAHEADPRICES], ids=lambda series: series.dataset)
def series_records(request, eds_client):
    series = request.param
    response = DatasetApi(eds_client, series.dataset).get(limit=RECENT_RECORDS)
    assert response.status_code == 200
    records = response.json()["records"]
    assert records, f"no {series.dataset} records to check"
    return series, records


@pytest.fixture(autouse=True)
def allure_feature_for_series(series_records):
    allure.dynamic.feature(series_records[0].dataset)


def utc_time(record, series):
    return dt.datetime.fromisoformat(record[series.time_field]).replace(tzinfo=dt.UTC)


def test_whenCheckingFreshness_thenTheNewestRecordIsRecentEnough(series_records):
    # arrange
    series, records = series_records
    oldest_acceptable = dt.datetime.now(dt.UTC) - series.max_lag

    # act
    newest = max(utc_time(record, series) for record in records)

    # assert
    assert newest >= oldest_acceptable, f"newest {series.time_field} is {newest}, older than {oldest_acceptable}"


def test_whenCheckingCompleteness_thenEveryAreaHasEveryStepWithoutGaps(series_records):
    # arrange
    series, records = series_records
    times_by_area = defaultdict(list)
    for record in records:
        times_by_area[record["PriceArea"]].append(utc_time(record, series))

    # act
    irregular_steps = {
        area: [(earlier, later) for earlier, later in pairwise(sorted(times)) if later - earlier != series.step]
        for area, times in times_by_area.items()
    }

    # assert
    assert {area: steps for area, steps in irregular_steps.items() if steps} == {}


def test_whenCheckingAreas_thenDk1AndDk2AreBothPresent(series_records):
    # arrange
    _, records = series_records

    # act
    areas = {record["PriceArea"] for record in records}

    # assert
    assert areas >= REQUIRED_AREAS, f"areas present: {sorted(areas)}"


def test_whenCheckingTimeZones_thenDanishTimeMatchesTheUtcTimestamp(series_records):
    # arrange
    series, records = series_records

    # act
    mismatches = [
        (record[series.time_field], record[series.local_time_field])
        for record in records
        if dt.datetime.fromisoformat(record[series.local_time_field])
        != utc_time(record, series).astimezone(COPENHAGEN).replace(tzinfo=None)
    ]

    # assert
    assert mismatches == []


def test_whenCheckingValues_thenTheyAreFiniteNumbersWithinThePlausibleRange(series_records):
    # arrange
    series, records = series_records
    low, high = series.value_range

    # act
    implausible = [
        value
        for value in (record[series.value_field] for record in records)
        if isinstance(value, bool) or not isinstance(value, int | float) or not math.isfinite(value) or not low <= value <= high
    ]

    # assert
    assert implausible == []


def test_whenParsingRecords_thenEveryRecordFitsTheTypedModel(series_records):
    # arrange
    series, records = series_records

    # act
    parsed = parse_records({"records": records}, series.model)

    # assert
    assert len(parsed) == len(records)
