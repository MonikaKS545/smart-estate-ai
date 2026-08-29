from fastapi import APIRouter
from pydantic import BaseModel
from app.services.forecasting import forecast_property_value

router = APIRouter(prefix="/forecasting", tags=["AI Price Forecasting"])

class ForecastRequest(BaseModel):
    current_price: float
    city: str
    years: int = 5

@router.post("/predict")
def predict_appreciation(req: ForecastRequest):
    return forecast_property_value(req.current_price, req.city, req.years)
