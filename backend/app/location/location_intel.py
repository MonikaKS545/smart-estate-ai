# NOTE: Public Overpass API servers (overpass-api.de, kumi.systems) were experiencing
# outages during development (Aug 2026 — see github.com/drolbr/Overpass-API/issues/791).
# Logic tested and confirmed working structurally; retry once servers recover to verify
# live data end-to-end.
import requests
from geopy.distance import geodesic

OVERPASS_URL = "https://overpass.kumi.systems/api/interpreter"

# Overpass tag mapping for each category we care about
CATEGORY_TAGS = {
    "schools": '["amenity"="school"]',
    "hospitals": '["amenity"="hospital"]',
    "metro": '["railway"="station"]',
    "bus_stops": '["highway"="bus_stop"]',
    "malls": '["shop"="mall"]',
    "restaurants": '["amenity"="restaurant"]',
    "parks": '["leisure"="park"]',
}

SEARCH_RADIUS_METERS = 2000


def build_query(lat, lon, tag_filter):
    return f"""
    [out:json][timeout:50];
    (
      node{tag_filter}(around:{SEARCH_RADIUS_METERS},{lat},{lon});
    );
    out center;
    """


import time

def fetch_category(lat, lon, category, retries=1):
    tag_filter = CATEGORY_TAGS[category]
    query = build_query(lat, lon, tag_filter)

    headers = {
        "User-Agent": "SmartEstateAI/1.0 (student project; contact: kavya@example.com)",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    last_error = None
    for attempt in range(retries):
        try:
            response = requests.post(OVERPASS_URL, data={"data": query}, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            break
        except Exception as e:
            last_error = e
            time.sleep(3)
    else:
        raise last_error

    results = []
    origin = (lat, lon)

    for element in data.get("elements", []):
        name = element.get("tags", {}).get("name", f"Unnamed {category[:-1]}")

        if element["type"] == "node":
            point = (element["lat"], element["lon"])
        elif "center" in element:
            point = (element["center"]["lat"], element["center"]["lon"])
        else:
            continue

        distance_km = round(geodesic(origin, point).km, 2)
        results.append({"name": name, "distance_km": distance_km})

    results.sort(key=lambda x: x["distance_km"])
    return results[:10]


def get_nearby_facilities(lat, lon):
    nearby = {}
    for category in CATEGORY_TAGS:
        try:
            nearby[category] = fetch_category(lat, lon, category)
        except Exception as e:
            print(f"Warning: failed to fetch {category}: {e}")
            nearby[category] = []
    return nearby


def compute_location_score(nearby):
    """Score 0-100 based on facility count and proximity across categories."""
    score = 0
    max_per_category = 100 / len(CATEGORY_TAGS)

    for category, places in nearby.items():
        if not places:
            continue

        count_score = min(len(places), 5) / 5

        closest_distance = places[0]["distance_km"]
        proximity_score = max(0, 1 - (closest_distance / 2.0))

        category_score = max_per_category * (0.5 * count_score + 0.5 * proximity_score)
        score += category_score

    return round(min(score, 100))


def get_location_intel(lat, lon):
    nearby = get_nearby_facilities(lat, lon)
    location_score = compute_location_score(nearby)
    return {
        "nearby": nearby,
        "location_score": location_score,
    }


if __name__ == "__main__":
    # Test with MG Road, Bengaluru coordinates
    result = get_location_intel(12.9758, 77.6045)
    for category, places in result["nearby"].items():
        print(f"{category}: {len(places)} found, closest: {places[0] if places else 'none'}")
    print("Location score:", result["location_score"])