import random
from app.database import SessionLocal, engine, Base
from app.models.user import User, RoleEnum
from app.models.property import Property, ListingTypeEnum, PropertyStatusEnum
from app.models.common import Amenity
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# --- Amenities ---
amenity_names = [
    "Swimming Pool", "Gym", "Parking", "24/7 Security", "Power Backup",
    "Lift", "Clubhouse", "Children's Play Area", "Garden", "CCTV",
    "Intercom", "Rainwater Harvesting", "Gas Pipeline", "Fire Safety", "Visitor Parking",
]

existing_amenities = {a.name for a in db.query(Amenity).all()}
for name in amenity_names:
    if name not in existing_amenities:
        db.add(Amenity(name=name))
db.commit()

# --- Sample agent user (only created if it doesn't exist) ---
agent_email = "seed.agent@example.com"
agent = db.query(User).filter(User.email == agent_email).first()
if not agent:
    agent = User(
        name="Seed Agent",
        email=agent_email,
        password_hash=hash_password("seedpass123"),
        role=RoleEnum.agent,
        is_verified=True,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)

# --- Sample properties ---
cities = ["Bengaluru", "Mumbai", "Delhi", "Pune", "Hyderabad", "Chennai"]
property_types = ["apartment", "villa", "independent house", "plot"]
furnishings = ["furnished", "semi-furnished", "unfurnished"]
titles = [
    "Spacious {bhk}BHK {ptype} in {city}",
    "Modern {bhk}BHK {ptype} near city center, {city}",
    "Luxury {bhk}BHK {ptype} with great amenities, {city}",
    "Cozy {bhk}BHK {ptype} in prime location, {city}",
]

existing_count = db.query(Property).count()

if existing_count < 5:
    for i in range(30):
        city = random.choice(cities)
        ptype = random.choice(property_types)
        bhk = random.choice([1, 2, 3, 4])
        listing_type = random.choice([ListingTypeEnum.buy, ListingTypeEnum.rent])
        title = random.choice(titles).format(bhk=bhk, ptype=ptype.title(), city=city)

        if listing_type == ListingTypeEnum.buy:
            price = round(random.uniform(3000000, 25000000), -3)
        else:
            price = round(random.uniform(10000, 80000), -2)

        new_property = Property(
            agent_id=agent.id,
            title=title,
            description=f"A beautiful {bhk}BHK {ptype} located in {city}, close to schools, hospitals, and markets.",
            property_type=ptype,
            listing_type=listing_type,
            price=price,
            area_sqft=round(random.uniform(600, 3000), 0),
            bhk=bhk,
            bathrooms=max(1, bhk - 1),
            floor=random.randint(0, 15),
            total_floors=random.randint(5, 20),
            property_age_years=random.randint(0, 15),
            furnishing=random.choice(furnishings),
            parking=random.choice([True, False]),
            latitude=round(random.uniform(8.0, 28.0), 4),
            longitude=round(random.uniform(72.0, 88.0), 4),
            address=f"{random.randint(1, 200)} Main Road, {city}",
            city=city,
            status=PropertyStatusEnum.approved,
        )
        db.add(new_property)

    db.commit()
    print("Seeded 30 properties and amenities successfully.")
else:
    print(f"Properties already exist ({existing_count} found) — skipping property seeding.")

db.close()