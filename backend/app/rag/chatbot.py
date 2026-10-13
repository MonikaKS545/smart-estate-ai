import os
import re
from dotenv import load_dotenv
from groq import Groq
from sqlalchemy import func
from app.rag.vector_store import search_properties
from app.models.property import Property, PropertyStatusEnum

load_dotenv()

_groq_client = None

def get_groq_client():
    global _groq_client
    if _groq_client is None:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return None
        _groq_client = Groq(api_key=api_key)
    return _groq_client

SYSTEM_PROMPT = """You are SmartEstate AI, a friendly and knowledgeable real estate assistant for Bengaluru, India.

RULES FOR EVERY REPLY:

1. Always be helpful and positive. Never reply with a bare "no", "I can't", "I don't have", "not available" or "no matching properties". Never leave the user at a dead end.

2. Property questions: use ONLY the listings provided in the context below. Never invent a property, price, locality, size or detail.
   - If there are exact matches, present them clearly.
   - If there are no exact matches, show the closest alternatives from the context (nearby locality, slightly different budget, different BHK) and say briefly how they differ from the request.
   - If the context is empty, give useful guidance instead (typical price ranges, good localities for the user's budget, what to check when buying) and invite the user to adjust budget, BHK or area so you can search again.

3. General questions (buying process, home loans, EMI, registration, stamp duty, documents, rental vs buy, localities, investment tips, greetings, small talk): answer directly from your own knowledge in a clear, practical way. Mention that figures such as rates and fees can change and should be verified.

4. Questions unrelated to real estate: answer briefly and helpfully, then smoothly steer back to how you can help with finding a property.

5. Vague or short messages (for example "hi", "help", "total properties"): reply warmly and suggest 3 example questions the user can ask, such as "2 BHK under 80 lakhs in Whitefield".

6. Format prices in lakhs or crores (for example ₹64.9 L, ₹1.2 Cr). Keep replies short, friendly and easy to scan. End with one helpful follow-up suggestion.

7. Be honest. If you are unsure about a fact, say what is generally true and suggest checking with an official source, rather than guessing. Never fabricate legal, financial or listing details."""

MODELS_TO_TRY = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama-3.1-70b-versatile",
    "mixtral-8x7b-32768",
    "openai/gpt-oss-120b",
]


def try_groq_completion(client, messages, temperature=0.3):
    last_err = None
    for model in MODELS_TO_TRY:
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
            )
            return completion.choices[0].message.content
        except Exception as e:
            last_err = e
            continue
    raise last_err or RuntimeError("No Groq models available")


# Simple keyword check for aggregate/counting questions — these can't be
# answered correctly by semantic search over a top-5 sample, so they're
# routed to a direct database count instead of the LLM/RAG path.
COUNT_PATTERNS = [
    r"\bhow many\b",
    r"\btotal (number of )?propert",
    r"\bnumber of propert",
    r"\bcount of propert",
]


def is_count_query(query: str) -> bool:
    q = query.lower()
    return any(re.search(pattern, q) for pattern in COUNT_PATTERNS)


def answer_count_query(db) -> dict:
    total = db.query(func.count(Property.id)).scalar()
    approved = (
        db.query(func.count(Property.id))
        .filter(Property.status == PropertyStatusEnum.approved)
        .scalar()
    )
    pending = (
        db.query(func.count(Property.id))
        .filter(Property.status == PropertyStatusEnum.pending)
        .scalar()
    )
    sold = (
        db.query(func.count(Property.id))
        .filter(Property.status == PropertyStatusEnum.sold)
        .scalar()
    )

    response_text = (
        f"We currently have {total} properties listed in total — "
        f"{approved} available, {pending} pending review, and {sold} sold. "
        f"Would you like me to find properties in a specific budget or area like Whitefield or Indiranagar?"
    )

    return {
        "response_text": response_text,
        "referenced_property_ids": [],
    }


def get_relevant_properties(query: str, top_k: int = 5):
    results = search_properties(query, top_k=top_k)

    properties = []
    ids = results["ids"][0]
    metadatas = results["metadatas"][0]
    documents = results["documents"][0]

    for i in range(len(ids)):
        properties.append({
            "property_id": ids[i],
            "metadata": metadatas[i],
            "text": documents[i],
        })

    return properties


def format_properties_for_prompt(properties):
    lines = []
    for p in properties:
        lines.append(f"- Property ID {p['property_id']}: {p['text']}")
    return "\n".join(lines)


def answer_query(query: str, top_k: int = 5, db=None):
    # Counting/aggregate questions bypass RAG entirely — they need a
    # real database count, not a 5-result semantic sample.
    if db is not None and is_count_query(query):
        return answer_count_query(db)

    client = get_groq_client()
    if not client:
        return {
            "response_text": "AI Assistant is currently unavailable because GROQ_API_KEY is not configured.",
            "referenced_property_ids": [],
        }

    matches = get_relevant_properties(query, top_k=top_k)

    if not matches:
        context = "(No matching property listings found in the database for this specific search query. Provide helpful guidance and suggest popular localities, typical prices, or alternative options according to your rules.)"
        referenced_ids = []
    else:
        context = format_properties_for_prompt(matches)
        referenced_ids = [p["property_id"] for p in matches]

    user_prompt = f"""User question: {query}

Available property data (use ONLY this listing data for specific property details):
{context}

Answer the user's question following all your system instructions."""

    try:
        response_text = try_groq_completion(
            client,
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
    except Exception as e:
        response_text = (
            "I'm here to help you explore properties and answer questions about real estate in Bengaluru! "
            "Could you tell me your preferred locality (e.g., Whitefield, Indiranagar, HSR Layout), BHK, or budget?"
        )

    return {
        "response_text": response_text,
        "referenced_property_ids": referenced_ids,
    }


def sync_chromadb_with_db(db):
    from app.models.property import Property, PropertyStatusEnum
    from app.rag.vector_store import upsert_property, reset_collection

    properties = (
        db.query(Property)
        .filter(Property.status == PropertyStatusEnum.approved)
        .all()
    )
    reset_collection()
    for p in properties:
        prop_type = (
            p.property_type.value
            if hasattr(p.property_type, "value")
            else str(p.property_type)
        )
        text = f"{p.title}. {p.description or ''}. {prop_type}. {p.bhk} BHK. {p.area_sqft} sqft. {p.address}. {p.city}. ₹{p.price:,.0f}."
        metadata = {
            "title": p.title,
            "price": float(p.price) if p.price else 0.0,
            "bhk": p.bhk if p.bhk else 0,
            "area_sqft": float(p.area_sqft) if p.area_sqft else 0.0,
            "city": p.city or "Bengaluru",
            "property_type": prop_type,
        }
        upsert_property(str(p.id), text, metadata)
    return len(properties)


if __name__ == "__main__":
    result = answer_query("affordable 3 BHK in Bangalore")
    print(result["response_text"])
    print("Referenced IDs:", result["referenced_property_ids"])