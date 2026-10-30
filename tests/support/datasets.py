from dataclasses import dataclass

from pydantic import BaseModel

from models.co2emis import CO2EmisRecord
from models.dayaheadprices import DayAheadPricesRecord


@dataclass(frozen=True)
class DatasetUnderTest:
    name: str
    sample_response_file: str
    schema_file: str
    optional_field: str
    required_field: str
    value_field: str
    model: type[BaseModel]


CO2EMIS_DATASET = DatasetUnderTest(
    "CO2Emis", "co2emis_sample.json", "co2emis_schema.json", "Minutes5DK", "Minutes5UTC", "CO2Emission", CO2EmisRecord
)
DAYAHEADPRICES_DATASET = DatasetUnderTest(
    "DayAheadPrices",
    "dayaheadprices_sample.json",
    "dayaheadprices_schema.json",
    "TimeUTC",
    "DayAheadPriceDKK",
    "DayAheadPriceDKK",
    DayAheadPricesRecord,
)
ALL_DATASETS = [CO2EMIS_DATASET, DAYAHEADPRICES_DATASET]
