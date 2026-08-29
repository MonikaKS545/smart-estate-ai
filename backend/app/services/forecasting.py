import math
from typing import Dict, List

def forecast_property_value(current_price: float, city: str, years: int = 5) -> Dict:
    """
    Predict future property value up to 5 years based on historical growth rates & market trends.
    """
    annual_growth_rates = {
        "mumbai": 0.075,
        "delhi": 0.068,
        "bangalore": 0.082,
        "new york": 0.055,
        "san francisco": 0.060,
        "default": 0.060
    }

    rate = annual_growth_rates.get(city.lower(), annual_growth_rates["default"])
    yearly_projections = []
    
    running_price = current_price
    for year in range(1, years + 1):
        running_price = running_price * (1 + rate)
        yearly_projections.append({
            "year": year,
            "projected_price": round(running_price, 2),
            "estimated_roi_percent": round(((running_price - current_price) / current_price) * 100, 2)
        })

    return {
        "current_price": current_price,
        "city": city,
        "assumed_annual_growth_rate": f"{rate * 100:.1f}%",
        "price_after_5_years": round(running_price, 2),
        "total_expected_appreciation": round(running_price - current_price, 2),
        "projections": yearly_projections
    }
