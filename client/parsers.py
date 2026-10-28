from typing import Any

from pydantic import BaseModel


def parse_records[ModelT: BaseModel](response_json: dict[str, Any], model: type[ModelT]) -> list[ModelT]:
    return [model(**record) for record in response_json["records"]]
