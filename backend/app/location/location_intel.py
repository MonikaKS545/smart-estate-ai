# NOTE: Public Overpass API servers (overpass-api.de, kumi.systems) were experiencing
# outages during development (Aug 2026 — see github.com/drolbr/Overpass-API/issues/791).
# Logic tested and confirmed working structurally against live data. A hardcoded
# FALLBACK_DATA set was added below so this feature never shows empty during a demo
# if all public Overpass mirrors are temporarily down — real live data is always tried
# first; the fallback only kicks in if every live attempt fails.
import time
import requests
from geopy.distance import geodesic

OVERPASS_URLS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

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

# Fallback: real, well-known facilities per major city, used only if every live
# Overpass mirror fails. Distances are realistic approximations, not computed from
# the exact property coordinates, since we have no live query to anchor them to.
FALLBACK_DATA = {
    "bengaluru": {
        "schools": [{"name": "National Public School", "distance_km": 0.9},
                    {"name": "Vidyashilp Academy", "distance_km": 1.6}],
        "hospitals": [{"name": "Manipal Hospital", "distance_km": 1.4},
                      {"name": "Columbia Asia Hospital", "distance_km": 2.1}],
        "metro": [{"name": "Whitefield Metro Station", "distance_km": 1.2}],
        "bus_stops": [{"name": "Whitefield Main Road Bus Stop", "distance_km": 0.3}],
        "malls": [{"name": "Phoenix Marketcity", "distance_km": 1.8},
                  {"name": "Forum Shantiniketan Mall", "distance_km": 2.4}],
        "restaurants": [{"name": "Truffles", "distance_km": 0.7},
                         {"name": "Meghana Foods", "distance_km": 1.1}],
        "parks": [{"name": "Whitefield Park", "distance_km": 0.6}],
    },
    "mumbai": {
        "schools": [{"name": "Bombay Scottish School", "distance_km": 1.1}],
        "hospitals": [{"name": "Lilavati Hospital", "distance_km": 2.0}],
        "metro": [{"name": "Andheri Metro Station", "distance_km": 1.5}],
        "bus_stops": [{"name": "Main Road Bus Stop", "distance_km": 0.4}],
        "malls": [{"name": "Infiniti Mall", "distance_km": 2.2}],
        "restaurants": [{"name": "Bademiya", "distance_km": 1.0}],
        "parks": [{"name": "Sanjay Gandhi National Park", "distance_km": 3.1}],
    },
    "delhi": {
        "schools": [{"name": "Delhi Public School", "distance_km": 1.3}],
        "hospitals": [{"name": "Max Super Speciality Hospital", "distance_km": 1.9}],
        "metro": [{"name": "Nearest Metro Station", "distance_km": 0.8}],
        "bus_stops": [{"name": "Main Road Bus Stop", "distance_km": 0.3}],
        "malls": [{"name": "Select Citywalk", "distance_km": 2.5}],
        "restaurants": [{"name": "Karim's", "distance_km": 1.2}],
        "parks": [{"name": "Lodhi Garden", "distance_km": 2.8}],
    },
    "chennai": {
        "schools": [{"name": "PSBB Senior Secondary School", "distance_km": 1.0}],
        "hospitals": [{"name": "Apollo Hospital", "distance_km": 1.7}],
        "metro": [{"name": "Nearest Metro Station", "distance_km": 1.4}],
        "bus_stops": [{"name": "Main Road Bus Stop", "distance_km": 0.3}],
        "malls": [{"name": "Phoenix Marketcity Chennai", "distance_km": 2.3}],
        "restaurants": [{"name": "Saravana Bhavan", "distance_km": 0.8}],
        "parks": [{"name": "Semmozhi Poonga", "distance_km": 2.6}],
    },
    "hyderabad": {
        "schools": [{"name": "Delhi Public School Hyderabad", "distance_km": 1.2}],
        "hospitals": [{"name": "Yashoda Hospital", "distance_km": 1.8}],
        "metro": [{"name": "Nearest Metro Station", "distance_km": 1.1}],
        "bus_stops": [{"name": "Main Road Bus Stop", "distance_km": 0.3}],
        "malls": [{"name": "Inorbit Mall", "distance_km": 2.0}],
        "restaurants": [{"name": "Paradise Biryani", "distance_km": 0.9}],
        "parks": [{"name": "KBR National Park", "distance_km": 2.9}],
    },
    "pune": {
        "schools": [{"name": "Symbiosis International School", "distance_km": 1.1}],
        "hospitals": [{"name": "Ruby Hall Clinic", "distance_km": 1.9}],
        "metro": [{"name": "Nearest Metro Station", "distance_km": 1.3}],
        "bus_stops": [{"name": "Main Road Bus Stop", "distance_km": 0.3}],
        "malls": [{"name": "Phoenix Marketcity Pune", "distance_km": 2.1}],
        "restaurants": [{"name": "Vaishali", "distance_km": 0.8}],
        "parks": [{"name": "Empress Garden", "distance_km": 2.4}],
    },
}


def build_query(lat, lon, tag_filter):
    return f"""
    [out:json][timeout:50];
    (
      node{tag_filter}(around:{SEARCH_RADIUS_METERS},{lat},{lon});
    );
    out center;
    """


def fetch_category(lat, lon, category, dead_mirrors):
    tag_filter = CATEGORY_TAGS[category]
    query = build_query(lat, lon, tag_filter)

    headers = {
        "User-Agent": "SmartEstateAI/1.0 (student project; contact: kavya@example.com)",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    # Circuit breaker: skip any mirror that already failed earlier in this same
    # request, instead of re-waiting out its full timeout for every category.
    # This keeps the whole request fast enough that it never starves a long-lived
    # DB connection (e.g. Neon) held open elsewhere in the same request.
    candidates = [u for u in OVERPASS_URLS if u not in dead_mirrors]

    for url in candidates:
        try:
            response = requests.post(url, data={"data": query}, headers=headers, timeout=6)
            response.raise_for_status()
            data = response.json()
            break
        except Exception as e:
            print(f"  Overpass mirror {url} failed for {category}: {e}")
            dead_mirrors.add(url)
            continue
    else:
        # every live (non-dead) mirror failed, or none were left to try
        return None

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


def get_nearby_facilities(lat, lon, city: str = ""):
    nearby = {}
    used_fallback = False
    city_key = (city or "").strip().lower()
    dead_mirrors = set()

    for category in CATEGORY_TAGS:
        live_result = fetch_category(lat, lon, category, dead_mirrors)
        if live_result is not None:
            nearby[category] = live_result
        else:
            print(f"Warning: all Overpass mirrors failed for {category}, using fallback data")
            fallback_city = FALLBACK_DATA.get(city_key, {})
            nearby[category] = fallback_city.get(category, [])
            used_fallback = True

    return nearby, used_fallback


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


def get_location_intel(lat, lon, city: str = ""):
    nearby, used_fallback = get_nearby_facilities(lat, lon, city)
    location_score = compute_location_score(nearby)
    return {
        "nearby": nearby,
        "location_score": location_score,
        "data_source": "fallback" if used_fallback else "live",
    }


if __name__ == "__main__":
    result = get_location_intel(12.9758, 77.6045, city="Bengaluru")
    for category, places in result["nearby"].items():
        print(f"{category}: {len(places)} found, closest: {places[0] if places else 'none'}")
    print("Location score:", result["location_score"])
    print("Data source:", result["data_source"])