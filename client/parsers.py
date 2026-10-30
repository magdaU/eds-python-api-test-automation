from typing import Any

from pydantic import BaseModel


class InvalidResponseError(ValueError):
    """The API answered with a body that is not the expected `{"records": [...]}` object."""


def parse_records[ModelT: BaseModel](response_json: Any, model: type[ModelT]) -> list[ModelT]:
    """The records of a dataset response as `model` objects.

    Raises `InvalidResponseError` when the body is not an object with a list under `records`,
    and `pydantic.ValidationError` when a record does not fit the model.
    """
    if not isinstance(response_json, dict) or not isinstance(response_json.get("records"), list):
        raise InvalidResponseError(f"expected a JSON object with a list under 'records', got {repr(response_json)[:100]}")
    return [model.model_validate(record) for record in response_json["records"]]
