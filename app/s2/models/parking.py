from datetime import datetime

from sqlalchemy import Boolean,DateTime,Integer
from sqlalchemy.orm import Mapped,mapped_column

from app.s2.database import Base

class ParkingSpot(Base):
    __tablename__= "parking_spots"
    
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    spot_number:Mapped[int]=mapped_column(Integer,unique=True,nullable=False)
    occupied:Mapped[bool]=mapped_column(Boolean,default=False,nullable=False)
    occupied_by:Mapped[int|None]=mapped_column(Integer,nullable=True)
    entry_time:Mapped[datetime|None]=mapped_column(DateTime,nullable=True)
