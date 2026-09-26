from fastapi import FastAPI

from app.s2.database import Base,engine
from app.s2.models.parking import ParkingSpot

from app.s2.routes.parking import router as parkingrouter

Base.metadata.create_all(bind=engine)

print("Database tables created.")

app = FastAPI()


app.include_router(parkingrouter,prefix="/s2")

@app.get("/")
def root():
    return {"service": "S2", "message": "Database service is running"}