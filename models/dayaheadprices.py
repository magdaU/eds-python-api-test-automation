from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class DayAheadPricesRecord(BaseModel):
    # optional on purpose: a record without a time is a data-quality finding (live data-quality tests), not a parsing failure
    TimeUTC: datetime | None = None
    # the areas seen in the dataset (Denmark and the neighbouring markets); a new one fails parsing on purpose
    PriceArea: Literal["DK1", "DK2", "DE", "NO2", "SE3", "SE4"]
    DayAheadPriceDKK: float
