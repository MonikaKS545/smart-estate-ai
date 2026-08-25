from typing import List, Optional

# Verhoeff Algorithm tables (UIDAI's real Aadhaar checksum)
_D = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,2,3,4,0,6,7,8,9,5],
    [2,3,4,0,1,7,8,9,5,6],
    [3,4,0,1,2,8,9,5,6,7],
    [4,0,1,2,3,9,5,6,7,8],
    [5,9,8,7,6,0,4,3,2,1],
    [6,5,9,8,7,1,0,4,3,2],
    [7,6,5,9,8,2,1,0,4,3],
    [8,7,6,5,9,3,2,1,0,4],
    [9,8,7,6,5,4,3,2,1,0],
]
_P = [
    [0,1,2,3,4,5,6,7,8,9],
    [1,5,7,6,2,8,3,0,9,4],
    [5,8,0,3,7,9,6,1,4,2],
    [8,9,1,6,0,4,3,5,2,7],
    [9,4,5,3,1,2,6,8,7,0],
    [4,2,8,6,5,7,3,9,0,1],
    [2,7,9,3,8,0,6,4,1,5],
    [7,0,4,6,9,1,3,2,5,8],
]


def validate_aadhaar(number: str) -> bool:
    """Check Aadhaar using the Verhoeff algorithm — same as UIDAI uses."""
    num = str(number).strip().replace(" ", "").replace("-", "")
    if not num.isdigit() or len(num) != 12:
        return False
    if num[0] in "01":
        return False
    c = 0
    for i, d in enumerate(reversed(num)):
        c = _D[c][_P[i % 8][int(d)]]
    return c == 0


CITY_PRICE = {
    "Whitefield": 6500, "Koramangala": 9500, "Indiranagar": 11000,
    "HSR Layout": 8500, "Marathahalli": 6000, "Electronic City": 5000,
    "Jayanagar": 10000, "Bannerghatta Road": 5500, "Hebbal": 7500,
    "JP Nagar": 7000, "Yelahanka": 5000, "Sarjapur Road": 6000,
    "Bellandur": 7000, "Banashankari": 8000, "BTM Layout": 7500,
    "Rajajinagar": 8500, "Basavanagudi": 9000, "Malleswaram": 10000,
    "Vijayanagar": 7000, "Hennur": 5500,
}


class FraudScorer:
    def score(self, property_type: str, listing_type: str, price: float,
              area_sqft: float, bhk: int, bedrooms: int, floor: int,
              total_floors: int, property_age_years: int, furnishing: str,
              parking: int, city: str, amenities: List[str],
              aadhar_number: Optional[str] = None) -> dict:

        flags    = []
        reasons  = []
        risk_pts = 0

        # Rule 1: Price vs market rate
        avg_sqft = CITY_PRICE.get(city, 7000)
        expected = avg_sqft * area_sqft
        if listing_type == "sale" and expected > 0:
            ratio = price / expected
            if ratio < 0.50:
                flags.append({"level": "high",
                              "reason": f"Price is {(1-ratio)*100:.0f}% below market rate for {city}"})
                reasons.append("Suspiciously low price — possible scam listing")
                risk_pts += 35
            elif ratio < 0.70:
                flags.append({"level": "medium",
                              "reason": "Price is significantly below market rate"})
                reasons.append("Price is below average — verify with owner before paying")
                risk_pts += 15

        # Rule 2: Floor exceeds total floors
        if floor > total_floors:
            flags.append({"level": "high",
                          "reason": f"Floor ({floor}) exceeds total floors ({total_floors})"})
            reasons.append("Invalid floor data — listing may be fabricated")
            risk_pts += 25

        # Rule 3: Area too small per BHK
        if bhk > 0 and (area_sqft / bhk) < 200:
            flags.append({"level": "medium",
                          "reason": f"Only {area_sqft/bhk:.0f} sqft per BHK — very small"})
            reasons.append("Area per BHK is suspiciously small")
            risk_pts += 15

        # Rule 4: Bedrooms vs BHK mismatch
        if abs(bedrooms - bhk) > 1:
            flags.append({"level": "low",
                          "reason": f"Bedrooms ({bedrooms}) does not match BHK ({bhk})"})
            risk_pts += 5

        # Rule 5: Villa with no parking
        if property_type == "villa" and parking == 0:
            flags.append({"level": "low", "reason": "Villa with zero parking is unusual"})
            risk_pts += 5

        # Aadhaar validation
        aadhar_valid = None
        if aadhar_number:
            aadhar_valid = validate_aadhaar(aadhar_number)
            if not aadhar_valid:
                flags.append({"level": "high",
                              "reason": "Aadhaar number failed checksum — likely fake"})
                reasons.append("Invalid Aadhaar number — owner identity not verified")
                risk_pts += 30
            else:
                reasons.append("Aadhaar number passed checksum validation")

        trust_score = max(0, 100 - risk_pts)
        risk_level  = "low" if trust_score >= 80 else ("medium" if trust_score >= 50 else "high")

        if not reasons:
            reasons.append("No suspicious indicators found. Listing appears genuine.")

        return {
            "trust_score":  trust_score,
            "risk_level":   risk_level,
            "flags":        flags,
            "reasons":      reasons,
            "aadhar_valid": aadhar_valid,
        }


fraud_scorer = FraudScorer()