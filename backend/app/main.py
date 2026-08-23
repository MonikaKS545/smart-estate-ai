from fastapi import FastAPI
from app.routers import auth

app = FastAPI(title="SmartEstate AI - Part 1")

app.include_router(auth.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "SmartEstate AI backend is running"}