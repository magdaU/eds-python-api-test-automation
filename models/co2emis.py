from pydantic import BaseModel


class CO2EmisRecord(BaseModel):
    Minutes5UTC: str
    Minutes5DK: str | None = None
    PriceArea: str
    CO2Emission: float
