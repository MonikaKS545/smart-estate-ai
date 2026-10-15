import os
import re
import json
import time
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from dotenv import load_dotenv
from groq import Groq
from sqlalchemy import func, or_, and_, cast, String
from sqlalchemy.orm import Session
from app.rag.vector_store import search_properties
from app.models.property import Property, PropertyStatusEnum, ListingTypeEnum
from app.models.common import LocationCache

load_dotenv()

_groq_client = None
_embedding_model = None
_query_cache = {}

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FAST_MODEL = "llama-3.1-8b-instant"
MAIN_MODEL = "llama-3.3-70b-versatile"
CACHE_TTL_SECONDS = 300


def get_groq_client():
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        _groq_client = Groq(api_key=api_key)
    return _groq_client


def get_available_models():
    """Return list of models to try in order of preference."""
    return [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",
        "mixtral-8x7b-32768",
    ]


def try_groq_completion(client, messages, temperature=0.3, max_tokens=500):
    """Try to get completion from Groq with fallback models."""
    if not client:
        return None, None
    
    for model_name in get_available_models():
        try:
            completion = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return completion.choices[0].message.content, model_name
        except Exception as e:
            print(f"Model {model_name} failed: {e}")
            continue
    return None, None


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


def get_cache_key(query: str) -> str:
    return hashlib.sha256(query.lower().strip().encode()).hexdigest()


def get_cached_answer(query: str) -> Optional[Dict]:
    key = get_cache_key(query)
    if key in _query_cache:
        cached, timestamp = _query_cache[key]
        if time.time() - timestamp < CACHE_TTL_SECONDS:
            return cached
    return None


def set_cached_answer(query: str, answer: Dict):
    key = get_cache_key(query)
    _query_cache[key] = (answer, time.time())


def rule_based_extract_filters(query: str, start_time: float) -> Dict[str, Any]:
    """Simple rule-based filter extraction when Groq is unavailable."""
    q = query.lower()
    filters = {
        "intent": "general",
        "bedrooms": None,
        "property_type": None,
        "listing_type": None,
        "city": None,
        "locality": None,
        "min_price": None,
        "max_price": None,
        "min_area_sqft": None,
        "max_area_sqft": None,
        "status": None,
        "keywords": query,
    }

    # Intent detection
    if re.search(r"\b(how many|count|number of)\b", q):
        filters["intent"] = "count"
    elif re.search(r"\b(show|list|find|display)\b", q):
        filters["intent"] = "list"

    # Bedrooms/BHK
    bhk_match = re.search(r"(\d+)\s*(bhk|bedroom)", q)
    if bhk_match:
        filters["bedrooms"] = int(bhk_match.group(1))

    # Property type
    for pt in ["apartment", "villa", "plot", "independent_house"]:
        if pt in q:
            filters["property_type"] = pt
            break

    # Listing type
    if "rent" in q:
        filters["listing_type"] = "rent"
    elif "buy" in q or "sale" in q:
        filters["listing_type"] = "buy"

    # Cities
    cities = ["bengaluru", "bangalore", "mumbai", "delhi", "chennai", "hyderabad", "pune", "kolkata", "ahmedabad"]
    for city in cities:
        if city in q:
            filters["city"] = city
            break

    # Price
    crore_match = re.search(r"under\s+([\d.]+)\s*crore", q)
    if crore_match:
        filters["max_price"] = float(crore_match.group(1)) * 10000000
    else:
        lakh_match = re.search(r"under\s+([\d.]+)\s*lakh", q)
        if lakh_match:
            filters["max_price"] = float(lakh_match.group(1)) * 100000
    
    crore_match2 = re.search(r"(above|over|more than)\s+([\d.]+)\s*crore", q)
    if crore_match2:
        filters["min_price"] = float(crore_match2.group(2)) * 10000000
    else:
        lakh_match2 = re.search(r"(above|over|more than)\s+([\d.]+)\s*lakh", q)
        if lakh_match2:
            filters["min_price"] = float(lakh_match2.group(2)) * 100000

    filters["_extraction_time_ms"] = int((time.time() - start_time) * 1000)
    return filters


SYSTEM_PROMPT = """You are a real estate assistant for SmartEstate AI.
You must answer ONLY using the property data provided below.
Never invent prices, locations, or properties that are not in the given data.
If there is no exact match for what the user asked, do not simply say no —
look at the provided data and mention the closest available alternatives instead
(e.g. a different BHK count, property type, or nearby area), clearly noting that
they are not an exact match. Only say you have nothing relevant if truly nothing
in the given data is reasonably close.
Keep answers concise and helpful."""


FILTER_EXTRACTION_PROMPT = """You are a query understanding system for a real estate platform.
Extract structured filters from the user's natural language question.

Return ONLY a JSON object with these fields (use null for unspecified):
{
  "intent": "count" | "list" | "compare" | "details" | "general",
  "bedrooms": integer or null,
  "property_type": "apartment" | "villa" | "plot" | "independent_house" | null,
  "listing_type": "buy" | "rent" | null,
  "city": string or null,
  "locality": string or null,
  "min_price": number or null,
  "max_price": number or null,
  "min_area_sqft": number or null,
  "max_area_sqft": number or null,
  "status": "approved" | "pending" | "sold" | null,
  "keywords": string or null
}

Rules:
- "how many" / "count" / "number of" -> intent: "count"
- "show me" / "list" / "find" -> intent: "list"
- "compare" -> intent: "compare"
- "details about" / "tell me about" -> intent: "details"
- Price in lakhs/crores: convert to actual numbers (1 crore = 10000000, 1 lakh = 100000)
- "under X" / "below X" / "less than X" -> max_price
- "above X" / "over X" / "more than X" -> min_price
- BHK / bedrooms -> bedrooms
- Property types: apartment, villa, plot, independent_house
- Cities: bengaluru, mumbai, delhi, chennai, hyderabad, pune, etc.
- If unsure, use null.

Examples:
- "How many 2 BHK flats in Bengaluru?" -> {"intent": "count", "bedrooms": 2, "city": "bengaluru", "property_type": "apartment", "listing_type": "buy", ...}
- "Show 3 BHK in Whitefield under 1 crore" -> {"intent": "list", "bedrooms": 3, "locality": "whitefield", "max_price": 10000000, ...}
- "How many properties under 50 lakhs?" -> {"intent": "count", "max_price": 5000000, ...}
- "What's the neighborhood like in Whitefield?" -> {"intent": "general", "keywords": "neighborhood whitefield", ...}"""


def extract_filters(query: str, db: Session) -> Dict[str, Any]:
    start_time = time.time()
    client = get_groq_client()
    if client:
        content, model_used = try_groq_completion(client, [
            {"role": "system", "content": FILTER_EXTRACTION_PROMPT},
            {"role": "user", "content": query},
        ], temperature=0.1, max_tokens=300)
        if content:
            print(f"Filter extraction used model: {model_used}")
            content = content.strip()
            filters = json.loads(content)
            filters["_extraction_time_ms"] = int((time.time() - start_time) * 1000)
            filters["_model_used"] = model_used
            return filters

    # Fallback: simple rule-based extraction
    print("Using fallback rule-based filter extraction")
    return rule_based_extract_filters(query, start_time)


def build_sql_query(filters: Dict[str, Any], db: Session):
    query = db.query(Property).filter(Property.status == PropertyStatusEnum.approved)

    if filters.get("bedrooms"):
        query = query.filter(Property.bhk == filters["bedrooms"])

    if filters.get("property_type"):
        pt = filters["property_type"]
        if pt == "independent_house":
            pt = "Independent House"
        query = query.filter(Property.property_type == pt)

    if filters.get("listing_type"):
        query = query.filter(Property.listing_type == filters["listing_type"])

    if filters.get("city"):
        query = query.filter(Property.city.ilike(f"%{filters['city']}%"))

    if filters.get("locality"):
        query = query.filter(
            or_(
                Property.address.ilike(f"%{filters['locality']}%"),
                Property.city.ilike(f"%{filters['locality']}%"),
            )
        )

    if filters.get("min_price"):
        query = query.filter(Property.price >= filters["min_price"])

    if filters.get("max_price"):
        query = query.filter(Property.price <= filters["max_price"])

    if filters.get("min_area_sqft"):
        query = query.filter(Property.area_sqft >= filters["min_area_sqft"])

    if filters.get("max_area_sqft"):
        query = query.filter(Property.area_sqft <= filters["max_area_sqft"])

    return query


def execute_structured_query(filters: Dict[str, Any], db: Session, limit: int = 5) -> Dict[str, Any]:
    start_time = time.time()
    query = build_sql_query(filters, db)

    if filters.get("intent") == "count":
        count = query.count()
        return {
            "type": "count",
            "count": count,
            "filters_applied": {k: v for k, v in filters.items() if v is not None and k != "_extraction_time_ms"},
            "query_time_ms": int((time.time() - start_time) * 1000),
        }

    properties = query.order_by(Property.created_at.desc()).limit(limit).all()

    def prop_to_dict(p):
        return {
            "id": str(p.id),
            "title": p.title,
            "price": float(p.price) if p.price else 0,
            "area_sqft": float(p.area_sqft) if p.area_sqft else 0,
            "bhk": p.bhk,
            "bathrooms": p.bathrooms,
            "address": p.address,
            "city": p.city,
            "property_type": p.property_type.value if hasattr(p.property_type, 'value') else p.property_type,
            "listing_type": p.listing_type,
            "status": p.status.value if hasattr(p.status, 'value') else p.status,
        }

    results = [prop_to_dict(p) for p in properties]

    return {
        "type": "list",
        "count": len(results),
        "total_matching": query.count(),
        "properties": results,
        "filters_applied": {k: v for k, v in filters.items() if v is not None and k != "_extraction_time_ms"},
        "query_time_ms": int((time.time() - start_time) * 1000),
    }


def format_properties_for_prompt(properties: List[Dict]) -> str:
    lines = []
    for p in properties:
        lines.append(
            f"- ID {p['id']}: {p['title']}, {p.get('bhk', '?')} BHK, "
            f"₹{p.get('price', 0):,.0f}, {p.get('area_sqft', 0):,.0f} sqft, "
            f"{p.get('address', 'Unknown')}, {p.get('city', 'Unknown')}"
        )
    return "\n".join(lines)


def answer_general_query(query: str, db: Session, filters: Dict) -> Dict:
    start_time = time.time()
    client = get_groq_client()
    if not client:
        return {
            "response_text": "AI Assistant is currently unavailable because GROQ_API_KEY is not configured.",
            "referenced_property_ids": [],
            "timing": {"total_ms": 0},
        }

    try:
        matches = search_properties(filters.get("keywords", query), top_k=5)
        properties = []
        for i in range(len(matches["ids"][0])):
            properties.append({
                "property_id": matches["ids"][0][i],
                "metadata": matches["metadatas"][0][i],
                "text": matches["documents"][0][i],
            })

        if not properties:
            return {
                "response_text": "I don't have any properties matching that in our database right now.",
                "referenced_property_ids": [],
                "timing": {"total_ms": int((time.time() - start_time) * 1000)},
            }

        context = format_properties_for_prompt(properties)

        user_prompt = f"""User question: {query}

Available property data (this is the ONLY data you may use to answer):
{context}

Answer the user's question using only the above data."""

        response_text, model_used = try_groq_completion(client, [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ], temperature=0.3)
        print(f"General query used model: {model_used}")
        return {
            "response_text": response_text,
            "referenced_property_ids": [p["property_id"] for p in properties],
            "timing": {
                "total_ms": int((time.time() - start_time) * 1000),
            },
        }
    except Exception as e:
        print(f"General query failed: {e}")
        return {
            "response_text": f"I encountered an error while processing your question: {str(e)}",
            "referenced_property_ids": [],
            "timing": {"total_ms": int((time.time() - start_time) * 1000)},
        }


def format_structured_answer(query: str, result: Dict, filters: Dict) -> Dict:
    if result["type"] == "count":
        filters_desc = []
        if filters.get("bedrooms"):
            filters_desc.append(f"{filters['bedrooms']} BHK")
        if filters.get("property_type"):
            filters_desc.append(filters["property_type"])
        if filters.get("city"):
            filters_desc.append(filters["city"])
        if filters.get("max_price"):
            cr = filters["max_price"] / 10000000
            if cr >= 1:
                filters_desc.append(f"under {cr:.1f} crore")
            else:
                filters_desc.append(f"under {int(filters['max_price']/100000)} lakh")

        filter_str = ", ".join(filters_desc) if filters_desc else "all properties"
        response = f"Found {result['count']} {filter_str} matching your criteria."
        
        if result["count"] > 0:
            response += " Would you like me to show you some of them?"

        return {
            "response_text": response,
            "referenced_property_ids": [],
            "timing": {"total_ms": result.get("query_time_ms", 0)},
        }

    if result["type"] == "list":
        if result["count"] == 0:
            return {
                "response_text": "No properties match your criteria. Try broadening your search.",
                "referenced_property_ids": [],
                "timing": {"total_ms": result.get("query_time_ms", 0)},
            }

        props = result["properties"]
        lines = [f"Found {result['total_matching']} matching properties (showing {len(props)}):\n"]
        for p in props:
            price_lakhs = p["price"] / 100000
            lines.append(
                f"- {p['title']} — {p.get('bhk', '?')} BHK, "
                f"₹{price_lakhs:.1f}L, {p.get('area_sqft', 0):,.0f} sqft, {p.get('address', 'Unknown')}"
            )
        
        if result["total_matching"] > len(props):
            lines.append(f"\n...and {result['total_matching'] - len(props)} more. Ask me to show more or filter further.")

        return {
            "response_text": "\n".join(lines),
            "referenced_property_ids": [p["id"] for p in props],
            "timing": {"total_ms": result.get("query_time_ms", 0)},
        }

    return {
        "response_text": "I couldn't process that request.",
        "referenced_property_ids": [],
        "timing": {"total_ms": 0},
    }


def answer_query(query: str, db: Session) -> Dict:
    start_time = time.time()

    cached = get_cached_answer(query)
    if cached:
        cached["timing"]["total_ms"] = int((time.time() - start_time) * 1000)
        cached["from_cache"] = True
        return cached

    extraction_start = time.time()
    filters = extract_filters(query, db)
    extraction_time = int((time.time() - extraction_start) * 1000)

    intent = filters.get("intent", "general")

    if intent in ["count", "list"]:
        db_start = time.time()
        result = execute_structured_query(filters, db)
        result["_extraction_time_ms"] = extraction_time
        result["_db_time_ms"] = int((time.time() - db_start) * 1000)
        formatted = format_structured_answer(query, result, filters)
        formatted["timing"]["extraction_ms"] = extraction_time
        formatted["timing"]["db_ms"] = result.get("query_time_ms", 0)
        formatted["filters_used"] = filters
        set_cached_answer(query, formatted)
        return formatted

    general_start = time.time()
    result = answer_general_query(query, db, filters)
    result["timing"]["extraction_ms"] = extraction_time
    result["timing"]["rag_ms"] = int((time.time() - general_start) * 1000)
    set_cached_answer(query, result)
    return result


def sync_chromadb_with_db(db: Session):
    properties = db.query(Property).filter(Property.status == PropertyStatusEnum.approved).all()
    from app.rag.vector_store import upsert_property, reset_collection
    
    reset_collection()
    for p in properties:
        text = f"{p.title}. {p.description or ''}. {p.property_type.value if hasattr(p.property_type, 'value') else p.property_type}. {p.bhk} BHK. {p.area_sqft} sqft. {p.address}. {p.city}. ₹{p.price:,.0f}."
        metadata = {
            "title": p.title,
            "price": float(p.price) if p.price else 0,
            "bhk": p.bhk,
            "area_sqft": float(p.area_sqft) if p.area_sqft else 0,
            "city": p.city,
            "property_type": p.property_type.value if hasattr(p.property_type, 'value') else p.property_type,
        }
        upsert_property(str(p.id), text, metadata)
    return len(properties)


if __name__ == "__main__":
    from app.database import get_db
    db = next(get_db())
    result = answer_query("How many 2 BHK flats in Bengaluru?", db)
    print(json.dumps(result, indent=2))