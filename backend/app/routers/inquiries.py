from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.property import Property
from app.models.inquiry import PropertyInquiry, InquiryStatusEnum
from app.schemas.inquiry import InquiryCreate, InquiryResponse

router = APIRouter(prefix="/inquiries", tags=["Inquiries & Tours"])

@router.post("/", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
def create_inquiry(
    payload: InquiryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prop = db.query(Property).filter(Property.id == payload.property_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    inquiry = PropertyInquiry(
        property_id=payload.property_id,
        buyer_id=current_user.id,
        agent_id=prop.agent_id,
        inquiry_type=payload.inquiry_type,
        message=payload.message,
        preferred_date=payload.preferred_date
    )
    db.add(inquiry)
    db.commit()
    db.refresh(inquiry)
    return inquiry

@router.get("/agent", response_model=List[InquiryResponse])
def get_agent_inquiries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all tour inquiries assigned to the logged-in agent."""
    return db.query(PropertyInquiry).filter(PropertyInquiry.agent_id == current_user.id).all()

@router.get("/buyer", response_model=List[InquiryResponse])
def get_buyer_inquiries(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all tour requests submitted by the logged-in buyer."""
    return db.query(PropertyInquiry).filter(PropertyInquiry.buyer_id == current_user.id).all()

@router.put("/{inquiry_id}/status")
def update_inquiry_status(
    inquiry_id: UUID,
    status_value: InquiryStatusEnum,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inquiry = db.query(PropertyInquiry).filter(PropertyInquiry.id == inquiry_id).first()
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    if inquiry.agent_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this inquiry")

    inquiry.status = status_value
    db.commit()
    return {"message": f"Inquiry status updated to {status_value}"}
