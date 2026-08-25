from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from app.routers import auth, properties
import os

app = FastAPI(title="SmartEstate AI - Part 1")

app.add_middleware(SessionMiddleware, secret_key=os.getenv("JWT_SECRET"))

app.include_router(auth.router, prefix="/api/v1")
app.include_router(properties.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "SmartEstate AI backend is running"}