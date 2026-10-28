from dataclasses import dataclass


@dataclass(frozen=True)
class DatasetUnderTest:
    name: str
    sample_response_file: str
    schema_file: str
    optional_field: str
    required_field: str


CO2EMIS_DATASET = DatasetUnderTest("CO2Emis", "co2emis_sample.json", "co2emis_schema.json", "Minutes5DK", "Minutes5UTC")
ELSPOTPRICES_DATASET = DatasetUnderTest(
    "Elspotprices", "elspotprices_sample.json", "elspotprices_schema.json", "HourUTC", "SpotPriceDKK"
)
ALL_DATASETS = [CO2EMIS_DATASET, ELSPOTPRICES_DATASET]
