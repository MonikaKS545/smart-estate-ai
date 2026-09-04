from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.property import Property
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse
from app.core.deps import get_current_user, require_role

from fastapi import UploadFile, File
import shutil
import uuid as uuid_lib
import os
from app.models.common import PropertyImage

router = APIRouter(prefix="/properties", tags=["properties"])


@router.post("", response_model=PropertyResponse)
def create_property(
    payload: PropertyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("agent", "admin")),
):
    new_property = Property(agent_id=current_user.id, **payload.model_dump())
    db.add(new_property)
    db.commit()
    db.refresh(new_property)
    return new_property


@router.get("")
def list_properties(
    city: Optional[str] = Query(None),
    listing_type: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None),
    max_price: Optional[float] = Query(None),
    bhk: Optional[int] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Property).filter(Property.status == "approved")

    if city:
        query = query.filter(Property.city.ilike(f"%{city}%"))
    if listing_type:
        query = query.filter(Property.listing_type == listing_type)
    if min_price is not None:
        query = query.filter(Property.price >= min_price)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
    if bhk is not None:
        query = query.filter(Property.bhk == bhk)

    total = query.count()
    properties = query.all()

    property_ids = [p.id for p in properties]
    images = db.query(PropertyImage).filter(PropertyImage.property_id.in_(property_ids)).all()
    images_by_property = {}
    for img in images:
        images_by_property.setdefault(img.property_id, []).append(img.image_url)

    results = []
    for p in properties:
        item = PropertyResponse.model_validate(p).model_dump()
        item["images"] = images_by_property.get(p.id, [])
        results.append(item)

    return {
        "properties": results,
        "total": total,
    }


@router.get("/{property_id}")
def get_property(property_id: UUID, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    images = (
        db.query(PropertyImage)
        .filter(PropertyImage.property_id == property_id)
        .all()
    )
    image_urls = [img.image_url for img in images]

    amenity_names = [a.name for a in prop.amenities] if hasattr(prop, "amenities") else []

    return {
        "property": PropertyResponse.model_validate(prop),
        "images": image_urls,
        "amenities": amenity_names,
    }


@router.put("/{property_id}", response_model=PropertyResponse)
def update_property(
    property_id: UUID,
    payload: PropertyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    if prop.agent_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to edit this property")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(prop, key, value)

    db.commit()
    db.refresh(prop)
    return prop


@router.delete("/{property_id}")
def delete_property(
    property_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    if prop.agent_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this property")

    db.delete(prop)
    db.commit()
    return {"message": "Property deleted successfully"}


@router.post("/{property_id}/images")
def upload_property_image(
    property_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    if prop.agent_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to add images to this property")

    os.makedirs("uploads", exist_ok=True)
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid_lib.uuid4()}.{file_extension}"
    file_path = os.path.join("uploads", unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    image_url = f"/uploads/{unique_filename}"
    new_image = PropertyImage(property_id=property_id, image_url=image_url)
    db.add(new_image)
    db.commit()
    db.refresh(new_image)

    return {"image_url": image_url}

