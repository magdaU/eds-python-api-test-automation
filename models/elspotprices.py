from pydantic import BaseModel


class ElspotpricesRecord(BaseModel):
    HourUTC: str | None = None
    PriceArea: str
    SpotPriceDKK: float
