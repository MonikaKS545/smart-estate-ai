from app.database import SessionLocal
from app.models.property import Property
from app.models.common import Amenity, PropertyAmenity, DocumentVerification, Document
from app.location.location_intel import get_location_intel
from app.recommendation.content_based import build_user_profile, score_property


# ---- REAL Part 2 calls (swapped in from mocks) ----

from ml.price_predictor import predictor
from ml.fraud_scorer import fraud_scorer


def get_property_amenity_names(db, property_obj: Property):
    rows = (
        db.query(Amenity.name)
        .join(PropertyAmenity, PropertyAmenity.amenity_id == Amenity.id)
        .filter(PropertyAmenity.property_id == property_obj.id)
        .all()
    )
    return [r[0] for r in rows]


def real_predict_price(db, property_obj: Property):
    """Calls Part 2's real price prediction model directly."""
    if not property_obj.price:
        return None
    try:
        amenities = get_property_amenity_names(db, property_obj)
        result = predictor.predict(
            property_type=property_obj.property_type or "apartment",
            listing_type=property_obj.listing_type.value if property_obj.listing_type else "buy",
            area_sqft=float(property_obj.area_sqft) if property_obj.area_sqft else 0,
            bhk=property_obj.bhk or 0,
            bedrooms=property_obj.bhk or 0,
            floor=property_obj.floor or 0,
            total_floors=property_obj.total_floors or 0,
            property_age_years=property_obj.property_age_years or 0,
            furnishing=property_obj.furnishing or "unfurnished",
            parking=1 if property_obj.parking else 0,
            city=property_obj.city or "",
            amenities=amenities,
        )
        return {
            "predicted_price": result.predicted_price,
            "difference_percent": result.difference_percent,
        }
    except Exception as e:
        print(f"Warning: real price prediction failed, skipping: {e}")
        return None


def real_fraud_score(db, property_obj: Property):
    """Calls Part 2's real fraud scoring model directly."""
    try:
        amenities = get_property_amenity_names(db, property_obj)
        result = fraud_scorer.score(
            property_type=property_obj.property_type or "apartment",
            listing_type=property_obj.listing_type.value if property_obj.listing_type else "buy",
            price=float(property_obj.price) if property_obj.price else 0,
            area_sqft=float(property_obj.area_sqft) if property_obj.area_sqft else 0,
            bhk=property_obj.bhk or 0,
            bedrooms=property_obj.bhk or 0,
            floor=property_obj.floor or 0,
            total_floors=property_obj.total_floors or 0,
            property_age_years=property_obj.property_age_years or 0,
            furnishing=property_obj.furnishing or "unfurnished",
            parking=1 if property_obj.parking else 0,
            city=property_obj.city or "",
            amenities=amenities,
        )
        return {
            "trust_score": result["trust_score"] if isinstance(result, dict) else result.trust_score,
            "risk_level": result["risk_level"] if isinstance(result, dict) else result.risk_level,
        }
    except Exception as e:
        print(f"Warning: real fraud scoring failed, using fallback: {e}")
        return {"trust_score": 50, "risk_level": "unknown"}


def get_document_score(db, property_id):
    """Uses REAL data if a document verification exists for this property (Part 3's table), else None."""
    doc = db.query(Document).filter(Document.property_id == property_id).first()
    if not doc:
        return None

    verification = db.query(DocumentVerification).filter(
        DocumentVerification.document_id == doc.id
    ).order_by(DocumentVerification.created_at.desc()).first()

    if not verification:
        return None

    if verification.status.value == "verified":
        return 100
    elif verification.status.value == "mismatch":
        return 30
    else:
        return 50  # pending


# ---- This part's own scoring logic ----

def get_amenity_score(db, property_obj: Property):
    count = db.query(PropertyAmenity).filter(PropertyAmenity.property_id == property_obj.id).count()
    total_amenities = db.query(Amenity).count()
    if total_amenities == 0:
        return 0
    return round(min(count / total_amenities, 1.0) * 100)


def get_price_score(price_prediction):
    """Score based on how close listed price is to predicted market price. Closer = higher score."""
    if not price_prediction:
        return None
    diff = abs(price_prediction["difference_percent"])
    if diff <= 5:
        return 100
    elif diff <= 10:
        return 80
    elif diff <= 20:
        return 60
    elif diff <= 35:
        return 40
    else:
        return 20


def get_requirement_match_score(db, user_id, property_obj: Property):
    """Reuses the content-based recommender's scoring for this specific user + property."""
    if not user_id:
        return None
    profile = build_user_profile(db, user_id)
    score, _ = score_property(profile, property_obj)
    return score


def generate_recommendation_text(overall_score, fraud_score_data, price_score):
    if fraud_score_data["risk_level"] == "high":
        return "Exercise caution: this listing shows signs of potential risk. Verify documents carefully before proceeding."
    if overall_score >= 80:
        return "This is a strong listing overall — good value, location, and trust indicators."
    elif overall_score >= 60:
        return "This is a reasonably solid listing, though a few factors could be better."
    else:
        return "This listing has some notable gaps — review the individual scores before deciding."


def analyze_property(property_id: str, user_id: str = None):
    db = SessionLocal()
    try:
        prop = db.query(Property).filter(Property.id == property_id).first()
        if not prop:
            return {"error": "Property not found"}

        # Real Part 2 calls
        price_prediction = real_predict_price(db, prop)
        fraud_data = real_fraud_score(db, prop)

        # Real DB-backed Part 3 check
        document_score = get_document_score(db, property_id)

        # This part's own logic
        location_result = get_location_intel(float(prop.latitude), float(prop.longitude)) if prop.latitude and prop.longitude else None
        location_score = location_result["location_score"] if location_result else 0

        amenity_score = get_amenity_score(db, prop)
        price_score = get_price_score(price_prediction)
        market_price_score = price_score  # derived from the same prediction
        fraud_score = fraud_data["trust_score"]
        requirement_match_score = get_requirement_match_score(db, user_id, prop)

        # Documented weighting (used for overall_score) — adjust if your presentation needs different emphasis
        weights = {
            "price_score": 0.20,
            "location_score": 0.20,
            "amenity_score": 0.10,
            "market_price_score": 0.15,
            "document_score": 0.15,
            "fraud_score": 0.15,
            "requirement_match_score": 0.05,
        }

        scores = {
            "price_score": price_score,
            "location_score": location_score,
            "amenity_score": amenity_score,
            "market_price_score": market_price_score,
            "document_score": document_score,
            "fraud_score": fraud_score,
            "requirement_match_score": requirement_match_score,
        }

        # Only average the weights of scores that actually exist (skip None values, e.g. no docs yet)
        total_weight = sum(weights[k] for k, v in scores.items() if v is not None)
        weighted_sum = sum(weights[k] * v for k, v in scores.items() if v is not None)
        overall_score = round(weighted_sum / total_weight) if total_weight > 0 else 0

        recommendation_text = generate_recommendation_text(overall_score, fraud_data, price_score)

        return {
            **scores,
            "overall_score": overall_score,
            "recommendation_text": recommendation_text,
        }
    finally:
        db.close()


if __name__ == "__main__":
    db = SessionLocal()
    try:
        test_prop = db.query(Property).first()
        if test_prop:
            print(f"Testing with property: {test_prop.title}")
            result = analyze_property(str(test_prop.id))
            for k, v in result.items():
                print(f"{k}: {v}")
        else:
            print("No properties found in DB")
    finally:
        db.close()