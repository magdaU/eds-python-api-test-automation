from typing import TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


def parse_records(response_json: dict, model: type[ModelT]) -> list[ModelT]:
    return [model(**record) for record in response_json["records"]]
