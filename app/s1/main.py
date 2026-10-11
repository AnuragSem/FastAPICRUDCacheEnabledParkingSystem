from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.s1.routes.parking import router as parking_router
from app.s1 import s2_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    await s2_client.start_s2_client()
    try:
        yield
    finally:
        await s2_client.close_s2_client()


app = FastAPI(lifespan=lifespan)

app.include_router(parking_router,prefix="/s1")

@app.get("/")
def root():
    return {"service": "S1", "message": "Client service is running"}