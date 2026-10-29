from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetUnderTest:
    name: str
    sample_response_file: str
    schema_file: str
    optional_field: str
    required_field: str


CO2EMIS_DATASET = DatasetUnderTest("CO2Emis", "co2emis_sample.json", "co2emis_schema.json", "Minutes5DK", "Minutes5UTC")
DAYAHEADPRICES_DATASET = DatasetUnderTest(
    "DayAheadPrices", "dayaheadprices_sample.json", "dayaheadprices_schema.json", "TimeUTC", "DayAheadPriceDKK"
)
ALL_DATASETS = [CO2EMIS_DATASET, DAYAHEADPRICES_DATASET]
