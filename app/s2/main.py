
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.s2.database import Base, engine
from app.s2.models.parking import ParkingSpot
from app.s2.routes.parking import router as parkingrouter


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created.")

    yield

    await engine.dispose()


app = FastAPI(lifespan=lifespan)

app.include_router(parkingrouter, prefix="/s2")


@app.get("/")
async def root():
    return {
        "service": "S2",
        "message": "Database service is running"
    }