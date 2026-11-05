"""The optional fields of the Pydantic models and the JSON Schemas must agree on what they accept.

Each optional field is checked in four situations: absent, null, a valid value and a value of the
wrong type. The verdicts of the model and of the schema are compared. Where they differ, the test
documents the current behaviour and its name ends in `_thenDisagreementIsKnown`. Those disagreements
are not yet decided: the contract of null is unknown (no mock, no documentation and no OpenAPI
description says whether these fields can be null), so neither side was changed. See the report of
the branch fix/models-schema-consistency.

Pydantic ignores fields it does not declare, so for `TimeDK` and `DayAheadPriceEUR` the model
accepts every value; those tests show that disagreement too.
"""

import jsonschema
from pydantic import BaseModel, ValidationError

from models.co2emis import CO2EmisRecord
from models.dayaheadprices import DayAheadPricesRecord
from tests.support.allure_labels import labels
from tests.support.schema import assert_matches_schema

pytestmark = labels("Dataset API", "Model and schema agreement", "critical")

CO2EMIS_DATASET = "CO2Emis"
CO2EMIS_SCHEMA = "co2emis_schema.json"
DAYAHEADPRICES_DATASET = "DayAheadPrices"
DAYAHEADPRICES_SCHEMA = "dayaheadprices_schema.json"

CO2EMIS_RECORD = {"Minutes5UTC": "2024-01-01T00:00:00", "PriceArea": "DK1", "CO2Emission": 100.1}
DAYAHEADPRICES_RECORD = {"PriceArea": "DK1", "DayAheadPriceDKK": 302.25}


def _verdicts(
    model: type[BaseModel], dataset: str, schema_file: str, record: dict[str, object]
) -> tuple[bool, bool]:
    """Whether the model and the schema accept the record, as (model, schema)."""
    try:
        model.model_validate(record)
        model_accepts = True
    except ValidationError:
        model_accepts = False

    body = {"records": [record], "total": 1, "limit": 1, "dataset": dataset}
    try:
        assert_matches_schema(body, schema_file)
        schema_accepts = True
    except jsonschema.ValidationError:
        schema_accepts = False

    return model_accepts, schema_accepts


# Minutes5DK (CO2EmisRecord, optional with default None; schema: optional string, no null)


def test_givenMinutes5DKAbsent_whenValidating_thenModelAndSchemaBothAccept():
    # arrange
    record = CO2EMIS_RECORD

    # act
    verdicts = _verdicts(CO2EmisRecord, CO2EMIS_DATASET, CO2EMIS_SCHEMA, record)

    # assert
    assert verdicts == (True, True)


def test_givenMinutes5DKNull_whenValidating_thenDisagreementIsKnown():
    # arrange
    # contract unknown: the model says null is allowed, the schema does not
    record = {**CO2EMIS_RECORD, "Minutes5DK": None}

    # act
    verdicts = _verdicts(CO2EmisRecord, CO2EMIS_DATASET, CO2EMIS_SCHEMA, record)

    # assert
    assert verdicts == (True, False)


def test_givenMinutes5DKValidDateTime_whenValidating_thenModelAndSchemaBothAccept():
    # arrange
    record = {**CO2EMIS_RECORD, "Minutes5DK": "2024-01-01T01:00:00"}

    # act
    verdicts = _verdicts(CO2EmisRecord, CO2EMIS_DATASET, CO2EMIS_SCHEMA, record)

    # assert
    assert verdicts == (True, True)


def test_givenMinutes5DKWrongTypeList_whenValidating_thenModelAndSchemaBothReject():
    # arrange
    record = {**CO2EMIS_RECORD, "Minutes5DK": ["2024-01-01T01:00:00"]}

    # act
    verdicts = _verdicts(CO2EmisRecord, CO2EMIS_DATASET, CO2EMIS_SCHEMA, record)

    # assert
    assert verdicts == (False, False)


def test_givenMinutes5DKWrongTypeNumber_whenValidating_thenDisagreementIsKnown():
    # arrange
    # pydantic reads a number as a unix timestamp, the schema wants a string
    record = {**CO2EMIS_RECORD, "Minutes5DK": 1704070800}

    # act
    verdicts = _verdicts(CO2EmisRecord, CO2EMIS_DATASET, CO2EMIS_SCHEMA, record)

    # assert
    assert verdicts == (True, False)


def test_givenMinutes5DKNotADateTime_whenValidating_thenDisagreementIsKnown():
    # arrange
    # the schema says only "string", so any text passes; pydantic parses it as a datetime
    record = {**CO2EMIS_RECORD, "Minutes5DK": "yesterday"}

    # act
    verdicts = _verdicts(CO2EmisRecord, CO2EMIS_DATASET, CO2EMIS_SCHEMA, record)

    # assert
    assert verdicts == (False, True)


# TimeUTC (DayAheadPricesRecord, optional with default None; schema: optional string, no null)


def test_givenTimeUTCAbsent_whenValidating_thenModelAndSchemaBothAccept():
    # arrange
    record = DAYAHEADPRICES_RECORD

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (True, True)


def test_givenTimeUTCNull_whenValidating_thenDisagreementIsKnown():
    # arrange
    # contract unknown: the model says null is allowed, the schema does not
    record = {**DAYAHEADPRICES_RECORD, "TimeUTC": None}

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (True, False)


def test_givenTimeUTCValidDateTime_whenValidating_thenModelAndSchemaBothAccept():
    # arrange
    record = {**DAYAHEADPRICES_RECORD, "TimeUTC": "2024-06-01T00:00:00"}

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (True, True)


def test_givenTimeUTCWrongTypeList_whenValidating_thenModelAndSchemaBothReject():
    # arrange
    record = {**DAYAHEADPRICES_RECORD, "TimeUTC": ["2024-06-01T00:00:00"]}

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (False, False)


def test_givenTimeUTCWrongTypeNumber_whenValidating_thenDisagreementIsKnown():
    # arrange
    # pydantic reads a number as a unix timestamp, the schema wants a string
    record = {**DAYAHEADPRICES_RECORD, "TimeUTC": 1717200000}

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (True, False)


def test_givenTimeUTCNotADateTime_whenValidating_thenDisagreementIsKnown():
    # arrange
    # the schema says only "string", so any text passes; pydantic parses it as a datetime
    record = {**DAYAHEADPRICES_RECORD, "TimeUTC": "yesterday"}

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (False, True)


# TimeDK (in the schema as an optional string; not declared in DayAheadPricesRecord, so pydantic
# ignores it and accepts any value)


def test_givenTimeDKAbsent_whenValidating_thenModelAndSchemaBothAccept():
    # arrange
    record = DAYAHEADPRICES_RECORD

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (True, True)


def test_givenTimeDKNull_whenValidating_thenDisagreementIsKnown():
    # arrange
    # the model does not read TimeDK at all, so null passes there; the schema rejects it
    record = {**DAYAHEADPRICES_RECORD, "TimeDK": None}

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (True, False)


def test_givenTimeDKValidDateTime_whenValidating_thenModelAndSchemaBothAccept():
    # arrange
    record = {**DAYAHEADPRICES_RECORD, "TimeDK": "2024-06-01T02:00:00"}

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (True, True)


def test_givenTimeDKWrongTypeList_whenValidating_thenDisagreementIsKnown():
    # arrange
    # the model ignores TimeDK, so the wrong type passes there; the schema rejects it
    record = {**DAYAHEADPRICES_RECORD, "TimeDK": ["2024-06-01T02:00:00"]}

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (True, False)


# DayAheadPriceEUR (in the schema as an optional number; not declared in DayAheadPricesRecord)


def test_givenDayAheadPriceEURAbsent_whenValidating_thenModelAndSchemaBothAccept():
    # arrange
    record = DAYAHEADPRICES_RECORD

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (True, True)


def test_givenDayAheadPriceEURNull_whenValidating_thenDisagreementIsKnown():
    # arrange
    # the model ignores DayAheadPriceEUR, so null passes there; the schema rejects it
    record = {**DAYAHEADPRICES_RECORD, "DayAheadPriceEUR": None}

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (True, False)


def test_givenDayAheadPriceEURValidNumber_whenValidating_thenModelAndSchemaBothAccept():
    # arrange
    record = {**DAYAHEADPRICES_RECORD, "DayAheadPriceEUR": 40.5}

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (True, True)


def test_givenDayAheadPriceEURWrongTypeString_whenValidating_thenDisagreementIsKnown():
    # arrange
    # the model ignores DayAheadPriceEUR, so the wrong type passes there; the schema rejects it
    record = {**DAYAHEADPRICES_RECORD, "DayAheadPriceEUR": "40.5"}

    # act
    verdicts = _verdicts(
        DayAheadPricesRecord, DAYAHEADPRICES_DATASET, DAYAHEADPRICES_SCHEMA, record
    )

    # assert
    assert verdicts == (True, False)
