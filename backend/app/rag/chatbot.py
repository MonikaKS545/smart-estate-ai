import os
from dotenv import load_dotenv
from groq import Groq
from app.rag.vector_store import search_properties

load_dotenv()

_groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are a real estate assistant for SmartEstate AI.
You must answer ONLY using the property data provided below.
Never invent prices, locations, or properties that are not in the given data.
If there is no exact match for what the user asked, do not simply say no —
look at the provided data and mention the closest available alternatives instead
(e.g. a different BHK count, property type, or nearby area), clearly noting that
they are not an exact match. Only say you have nothing relevant if truly nothing
in the given data is reasonably close.
Keep answers concise and helpful."""


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


def answer_query(query: str, top_k: int = 5):
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

    completion = _groq_client.chat.completions.create(
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