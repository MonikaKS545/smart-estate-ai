import random
import uuid
from datetime import datetime
from app.database import SessionLocal
from app.models.user import User
from app.models.property import Property
from app.models.common import Document, DocumentVerification, VerificationStatusEnum, FraudAnalysis

def seed_property_verifications():
    db = SessionLocal()
    try:
        properties = db.query(Property).all()
        if not properties:
            print("No properties found in database to verify.")
            return

        admin_or_agent = db.query(User).first()
        uploader_id = admin_or_agent.id if admin_or_agent else None

        print(f"Seeding verification records for {len(properties)} properties...")

        # Delete old verification records to re-seed cleanly
        existing_doc_ids = [d.id for d in db.query(Document).all()]
        if existing_doc_ids:
            db.query(DocumentVerification).filter(DocumentVerification.document_id.in_(existing_doc_ids)).delete(synchronize_session=False)
        db.query(Document).delete(synchronize_session=False)
        db.query(FraudAnalysis).delete(synchronize_session=False)
        db.commit()

        # Seed distribution:
        # Tier 1 (High Trust, ~60%): score 85-96, verified RERA, nil encumbrance, clear title, complete docs, matched owner
        # Tier 2 (Partial, ~25%): score 55-70, verified RERA, pending encumbrance, partial docs
        # Tier 3 (Unverified, ~15%): score 0, no docs submitted ("Needs Verification")

        num_props = len(properties)
        tier1_count = int(num_props * 0.60)
        tier2_count = int(num_props * 0.25)
        # remainder is tier 3

        for index, prop in enumerate(properties):
            if index < tier1_count:
                # --- High Trust ---
                score = random.randint(85, 96)
                signals = {
                    "rera_status": "verified",
                    "encumbrance_status": "clear",
                    "title_clarity": "clear",
                    "document_completeness": 1.0,
                    "owner_match": "match",
                }

                # Create 3 documents
                doc_types = ["sale_deed", "encumbrance_cert", "tax_receipt"]
                for dt in doc_types:
                    doc = Document(
                        id=uuid.uuid4(),
                        property_id=prop.id,
                        uploaded_by=uploader_id,
                        doc_type=dt,
                        file_url=f"/uploads/documents/sample_{dt}_{prop.id}.pdf",
                        uploaded_at=datetime.utcnow()
                    )
                    db.add(doc)
                    db.flush()

                    verif = DocumentVerification(
                        id=uuid.uuid4(),
                        document_id=doc.id,
                        extracted_json={
                            "owner_name": "Verified Owner",
                            "property_address": prop.address,
                            "survey_number": f"SY-{random.randint(100, 999)}/A",
                            "registration_number": f"REG/2023/{random.randint(1000, 9999)}",
                        },
                        match_result_json=[
                            {"field": "owner_name", "status": "match"},
                            {"field": "property_address", "status": "match"},
                            {"field": "survey_number", "status": "match"},
                            {"field": "registration_number", "status": "match"},
                        ],
                        status=VerificationStatusEnum.verified,
                        created_at=datetime.utcnow()
                    )
                    db.add(verif)

                db.add(FraudAnalysis(
                    id=uuid.uuid4(),
                    property_id=prop.id,
                    trust_score=score,
                    risk_level="low",
                    reasons_json={
                        "trust_signals": signals,
                        "notes": "Full documentation verified with nil encumbrance."
                    },
                    created_at=datetime.utcnow()
                ))

            elif index < tier1_count + tier2_count:
                # --- Partial Trust ---
                score = random.randint(55, 70)
                signals = {
                    "rera_status": "verified",
                    "encumbrance_status": "pending",
                    "title_clarity": "clear",
                    "document_completeness": 0.70,
                    "owner_match": "match",
                }

                doc = Document(
                    id=uuid.uuid4(),
                    property_id=prop.id,
                    uploaded_by=uploader_id,
                    doc_type="sale_deed",
                    file_url=f"/uploads/documents/sample_sale_deed_{prop.id}.pdf",
                    uploaded_at=datetime.utcnow()
                )
                db.add(doc)
                db.flush()

                verif = DocumentVerification(
                    id=uuid.uuid4(),
                    document_id=doc.id,
                    extracted_json={
                        "owner_name": "Pending Verification Owner",
                        "property_address": prop.address,
                    },
                    match_result_json=[
                        {"field": "owner_name", "status": "match"},
                        {"field": "property_address", "status": "match"},
                    ],
                    status=VerificationStatusEnum.pending,
                    created_at=datetime.utcnow()
                )
                db.add(verif)

                db.add(FraudAnalysis(
                    id=uuid.uuid4(),
                    property_id=prop.id,
                    trust_score=score,
                    risk_level="medium",
                    reasons_json={
                        "trust_signals": signals,
                        "notes": "Sale deed submitted; encumbrance certificate in review."
                    },
                    created_at=datetime.utcnow()
                ))

            else:
                # --- Tier 3: Unverified / Needs Verification ---
                signals = {
                    "rera_status": None,
                    "encumbrance_status": None,
                    "title_clarity": None,
                    "document_completeness": None,
                    "owner_match": None,
                }
                db.add(FraudAnalysis(
                    id=uuid.uuid4(),
                    property_id=prop.id,
                    trust_score=0,
                    risk_level="unverified",
                    reasons_json={
                        "trust_signals": signals,
                        "notes": "No documents submitted yet."
                    },
                    created_at=datetime.utcnow()
                ))

        db.commit()
        print(f"Successfully seeded verification records for all {len(properties)} properties!")
        print(f"  - High Trust (85-96): {tier1_count} listings")
        print(f"  - Partial Checks (55-70): {tier2_count} listings")
        print(f"  - Needs Verification (0): {num_props - tier1_count - tier2_count} listings")

    except Exception as e:
        db.rollback()
        print(f"Error seeding verification data: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    seed_property_verifications()
