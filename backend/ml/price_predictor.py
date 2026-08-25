import joblib
import numpy as np
import os
from typing import List

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "price_model.pkl")

CITY_AVG_SQFT = {
    "Whitefield": 6500, "Koramangala": 9500, "Indiranagar": 11000,
    "HSR Layout": 8500, "Marathahalli": 6000, "Electronic City": 5000,
    "Jayanagar": 10000, "Bannerghatta Road": 5500, "Hebbal": 7500,
    "JP Nagar": 7000, "Yelahanka": 5000, "Sarjapur Road": 6000,
    "Bellandur": 7000, "Banashankari": 8000, "BTM Layout": 7500,
    "Rajajinagar": 8500, "Basavanagudi": 9000, "Malleswaram": 10000,
    "Vijayanagar": 7000, "Hennur": 5500,
}


class PricePredictor:
    def __init__(self):
        self._a = None

    def _load(self):
        if self._a is None:
            self._a = joblib.load(MODEL_PATH)

    def _encode(self, col: str, value: str):
        enc = self._a["encoders"][col]
        return enc.transform([value])[0] if value in enc.classes_ else 0

    def predict(self, property_type: str, listing_type: str, area_sqft: float,
                bhk: int, bedrooms: int, floor: int, total_floors: int,
                property_age_years: int, furnishing: str, parking: int,
                city: str, amenities: List[str]) -> dict:
        self._load()

        X = np.array([[
            self._encode("property_type", property_type),
            self._encode("furnishing", furnishing),
            self._encode("city", city),
            area_sqft, bhk, bedrooms, floor, total_floors,
            property_age_years, parking, len(amenities)
        ]])
        X_s = self._a["scaler"].transform(X)
        predicted = float(self._a["model"].predict(X_s)[0])

        avg = CITY_AVG_SQFT.get(city, 7000) * area_sqft
        diff_pct = ((predicted - avg) / max(avg, 1)) * 100

        if diff_pct > 10:
            insight = (f"This property is priced {abs(diff_pct):.1f}% above the average "
                       f"market rate in {city}. It may be premium due to location or features.")
        elif diff_pct < -10:
            insight = (f"This property is priced {abs(diff_pct):.1f}% below the average "
                       f"market rate in {city}. Good deal - verify the condition.")
        else:
            insight = (f"This property is fairly priced, within {abs(diff_pct):.1f}% "
                       f"of the average market rate in {city}.")

        return {
            "predicted_price": round(predicted, -3),
            "difference_percent": round(diff_pct, 2),
            "insight_text": insight,
        }


predictor = PricePredictor()