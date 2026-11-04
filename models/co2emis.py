from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class CO2EmisRecord(BaseModel):
    """One 5-minute CO2 emission record of the `CO2Emis` dataset, per price area."""

    Minutes5UTC: datetime
    Minutes5DK: datetime | None = None
    PriceArea: Literal["DK1", "DK2"]
    CO2Emission: float
