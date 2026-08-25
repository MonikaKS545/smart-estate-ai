from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime


class PropertyCreate(BaseModel):
    title: str
    description: Optional[str] = None
    property_type: Optional[str] = None
    listing_type: str  # "buy" or "rent"
    price: float
    area_sqft: Optional[float] = None
    bhk: Optional[int] = None
    bathrooms: Optional[int] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    property_age_years: Optional[int] = None
    furnishing: Optional[str] = None
    parking: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    listing_type: Optional[str] = None
    price: Optional[float] = None
    area_sqft: Optional[float] = None
    bhk: Optional[int] = None
    bathrooms: Optional[int] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    property_age_years: Optional[int] = None
    furnishing: Optional[str] = None
    parking: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    status: Optional[str] = None


class PropertyResponse(BaseModel):
    id: UUID
    agent_id: Optional[UUID]
    title: str
    description: Optional[str]
    property_type: Optional[str]
    listing_type: Optional[str]
    price: float
    area_sqft: Optional[float]
    bhk: Optional[int]
    bathrooms: Optional[int]
    floor: Optional[int]
    total_floors: Optional[int]
    property_age_years: Optional[int]
    furnishing: Optional[str]
    parking: Optional[bool]
    latitude: Optional[float]
    longitude: Optional[float]
    address: Optional[str]
    city: Optional[str]
    status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True