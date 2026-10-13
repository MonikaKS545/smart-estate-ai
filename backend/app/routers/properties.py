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
from app.models.common import PropertyImage, Document, DocumentVerification, FraudAnalysis

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


def get_properties_trust_map(db: Session, property_ids: List[UUID]):
    if not property_ids:
        return {}

    fraud_records = db.query(FraudAnalysis).filter(FraudAnalysis.property_id.in_(property_ids)).all()
    fraud_by_prop = {f.property_id: f for f in fraud_records}

    docs = db.query(Document).filter(Document.property_id.in_(property_ids)).all()
    docs_by_prop = {}
    for d in docs:
        docs_by_prop.setdefault(d.property_id, []).append(d)

    all_doc_ids = [d.id for d in docs]
    verifications = (
        db.query(DocumentVerification)
        .filter(DocumentVerification.document_id.in_(all_doc_ids))
        .all()
        if all_doc_ids else []
    )
    verifs_by_doc = {v.document_id: v for v in verifications}

    trust_map = {}
    for pid in property_ids:
        fraud = fraud_by_prop.get(pid)
        p_docs = docs_by_prop.get(pid, [])
        p_verifs = [verifs_by_doc[d.id] for d in p_docs if d.id in verifs_by_doc]

        # 1. If precomputed trust_signals exist in FraudAnalysis reasons_json
        if fraud and fraud.reasons_json and isinstance(fraud.reasons_json, dict) and "trust_signals" in fraud.reasons_json:
            trust_map[pid] = (fraud.reasons_json["trust_signals"], fraud.trust_score or 0)
            continue

        # 2. Derive from documents & verifications if present
        if p_verifs:
            has_verified = any(v.status.value == "verified" for v in p_verifs)
            has_mismatch = any(v.status.value == "mismatch" for v in p_verifs)
            doc_types = {d.doc_type for d in p_docs}
            completeness = min(1.0, round(len(doc_types) / 3.0, 2))

            signals = {
                "rera_status": "verified" if has_verified else ("pending" if not has_mismatch else "unregistered"),
                "encumbrance_status": "clear" if ("encumbrance_cert" in doc_types or has_verified) else "pending",
                "title_clarity": "clear" if has_verified else ("disputed" if has_mismatch else "pending"),
                "document_completeness": completeness,
                "owner_match": "match" if has_verified else ("mismatch" if has_mismatch else "pending"),
            }
            score = fraud.trust_score if (fraud and fraud.trust_score is not None) else (85 if has_verified else 50)
            trust_map[pid] = (signals, score)
            continue

        # 3. Default unverified state
        default_signals = {
            "rera_status": None,
            "encumbrance_status": None,
            "title_clarity": None,
            "document_completeness": None,
            "owner_match": None,
        }
        trust_map[pid] = (default_signals, 0)

    return trust_map


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

    trust_map = get_properties_trust_map(db, property_ids)

    results = []
    for p in properties:
        item = PropertyResponse.model_validate(p).model_dump()
        item["images"] = images_by_property.get(p.id, [])
        signals, score = trust_map.get(p.id, ({}, 0))
        item["trust_signals"] = signals
        item["trust_score"] = score
        results.append(item)

    return {
        "properties": results,
        "total": total,
    }

@router.get("/mine")
def list_my_properties(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    properties = db.query(Property).filter(Property.agent_id == current_user.id).all()

    property_ids = [p.id for p in properties]
    images = db.query(PropertyImage).filter(PropertyImage.property_id.in_(property_ids)).all()
    images_by_property = {}
    for img in images:
        images_by_property.setdefault(img.property_id, []).append(img.image_url)

    trust_map = get_properties_trust_map(db, property_ids)

    results = []
    for p in properties:
        item = PropertyResponse.model_validate(p).model_dump()
        item["images"] = images_by_property.get(p.id, [])
        signals, score = trust_map.get(p.id, ({}, 0))
        item["trust_signals"] = signals
        item["trust_score"] = score
        results.append(item)

    return {"properties": results}
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

    trust_map = get_properties_trust_map(db, [property_id])
    signals, score = trust_map.get(property_id, ({}, 0))

    prop_dict = PropertyResponse.model_validate(prop).model_dump()
    prop_dict["trust_signals"] = signals
    prop_dict["trust_score"] = score

    return {
        "property": prop_dict,
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

