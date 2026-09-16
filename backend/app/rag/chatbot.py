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

SYSTEM_PROMPT = """You are a real estate assistant for SmartEstate AI.
You must answer ONLY using the property data provided below.
Never invent prices, locations, or properties that are not in the given data.
If there is no exact match for what the user asked, do not simply say no —
look at the provided data and mention the closest available alternatives instead
(e.g. a different BHK count, property type, or nearby area), clearly noting that
they are not an exact match. Only say you have nothing relevant if truly nothing
in the given data is reasonably close.
Keep answers concise and helpful."""

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
        f"{approved} available, {pending} pending review, and {sold} sold."
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
        return {
            "response_text": "I don't have any properties matching that in our database right now.",
            "referenced_property_ids": [],
        }

    context = format_properties_for_prompt(matches)

    user_prompt = f"""User question: {query}

Available property data (this is the ONLY data you may use to answer):
{context}

Answer the user's question using only the above data."""

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    response_text = completion.choices[0].message.content

    return {
        "response_text": response_text,
        "referenced_property_ids": [p["property_id"] for p in matches],
    }


if __name__ == "__main__":
    result = answer_query("affordable 3 BHK in Bangalore")
    print(result["response_text"])
    print("Referenced IDs:", result["referenced_property_ids"])