from fastapi import FastAPI

from app.s1.routes.parking import router as parking_router

app = FastAPI()

app.include_router(parking_router,prefix="/s1")

@app.get("/")
def root():
    return {"service": "S1", "message": "Client service is running"}