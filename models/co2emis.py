from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CO2EmisRecord(BaseModel):
    Minutes5UTC: datetime
    Minutes5DK: datetime | None = None
    PriceArea: Literal["DK1", "DK2"]
    CO2Emission: float
