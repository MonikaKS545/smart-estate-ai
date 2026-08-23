import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime, Enum, ForeignKey, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class PropertyImage(Base):
    __tablename__ = "property_images"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"))
    image_url = Column(String, nullable=False)
    is_primary = Column(Boolean, default=False)


class Amenity(Base):
    __tablename__ = "amenities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)


class PropertyAmenity(Base):
    __tablename__ = "property_amenities"
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"), primary_key=True)
    amenity_id = Column(UUID(as_uuid=True), ForeignKey("amenities.id"), primary_key=True)


class Favorite(Base):
    __tablename__ = "favorites"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


class SavedSearch(Base):
    __tablename__ = "saved_searches"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    filters_json = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class PropertyView(Base):
    __tablename__ = "property_views"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"))
    viewed_at = Column(DateTime, default=datetime.utcnow)


class Document(Base):
    __tablename__ = "documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"))
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    doc_type = Column(String)
    file_url = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)


class VerificationStatusEnum(str, enum.Enum):
    verified = "verified"
    mismatch = "mismatch"
    pending = "pending"


class DocumentVerification(Base):
    __tablename__ = "document_verifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"))
    extracted_json = Column(JSONB)
    match_result_json = Column(JSONB)
    status = Column(Enum(VerificationStatusEnum), default=VerificationStatusEnum.pending)
    created_at = Column(DateTime, default=datetime.utcnow)


class FraudAnalysis(Base):
    __tablename__ = "fraud_analysis"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"))
    trust_score = Column(Integer)
    risk_level = Column(String)
    reasons_json = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)


class PricePrediction(Base):
    __tablename__ = "price_predictions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"))
    predicted_price = Column(Numeric)
    difference_percent = Column(Numeric)
    model_version = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"))
    match_score = Column(Integer)
    reason_text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)



class Report(Base):
    __tablename__ = "reports"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id = Column(UUID(as_uuid=True), ForeignKey("properties.id"))
    reported_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reason = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    started_at = Column(DateTime, default=datetime.utcnow)


class SenderEnum(str, enum.Enum):
    user = "user"
    assistant = "assistant"


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id"))
    sender = Column(Enum(SenderEnum))
    message_text = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)