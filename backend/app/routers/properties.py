from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.models.property import Property
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse
from app.core.deps import get_current_user, require_role

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

    return {
        "properties": [PropertyResponse.model_validate(p) for p in properties],
        "total": total,
    }


@router.get("/{property_id}")
def get_property(property_id: UUID, db: Session = Depends(get_db)):
    prop = db.query(Property).filter(Property.id == property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return {
        "property": PropertyResponse.model_validate(prop),
        "images": [],
        "amenities": [],
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