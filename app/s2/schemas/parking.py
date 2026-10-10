from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ParkingSpotCreate(BaseModel):
    spot_number: int


class ParkingSpotUpdate(BaseModel):
    occupied: bool
    occupied_by: int | None = None


class ParkingSpotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    spot_number: int
    occupied: bool
    occupied_by: int | None
    entry_time: datetime | None

