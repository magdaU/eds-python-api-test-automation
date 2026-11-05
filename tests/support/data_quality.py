"""Helpers for data-quality checks: a finding about the data is reported as DataQualityError."""

import datetime as dt


class DataQualityError(ValueError):
    """A record breaks the data contract (missing, null, wrong type or unparsable time).

    It is a finding about the data, not a bug in the check, so its message names the dataset
    and the field.
    """


def utc_time(record, series):
    """The UTC instant of `record[series.time_field]`, for the dataset named by `series.dataset`.

    Rules:
    - A timestamp with an offset (`Z`, `+01:00`, ...) is converted to UTC with `astimezone`,
      so the instant is the same and the hour is shifted to UTC.
    - A timestamp WITHOUT an offset is UTC. This is an assumption, not a conversion: the EDS
      fields are named `Minutes5UTC` and `TimeUTC`, and the live API returns naive values such
      as `2026-11-05T09:05:00` for them. Any other naive field would need its own rule.
    - A missing field, a None value, a non-string value and a string that is not ISO 8601
      raise DataQualityError, and the message names the dataset and the field.
    """
    dataset = series.dataset
    field = series.time_field
    if field not in record:
        raise DataQualityError(f"{dataset}: record has no field {field!r}")
    value = record[field]
    if value is None:
        raise DataQualityError(f"{dataset}: field {field!r} is None")
    if not isinstance(value, str):
        raise DataQualityError(
            f"{dataset}: field {field!r} must be a string, got {type(value).__name__}"
        )
    try:
        parsed = dt.datetime.fromisoformat(value)
    except ValueError as error:
        raise DataQualityError(
            f"{dataset}: field {field!r} is not an ISO 8601 timestamp: {value!r}"
        ) from error
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.UTC)
    return parsed.astimezone(dt.UTC)
