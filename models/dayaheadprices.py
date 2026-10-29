from pydantic import BaseModel


class DayAheadPricesRecord(BaseModel):
    TimeUTC: str | None = None
    PriceArea: str
    DayAheadPriceDKK: float
