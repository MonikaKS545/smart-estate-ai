import re
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Rapidfuzz fuzzy string matching
RAPIDFUZZ_AVAILABLE = False
try:
    from rapidfuzz import fuzz
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    logger.warning("rapidfuzz library not found. Falling back to basic string similarity.")


MANDATORY_DISCLAIMER = (
    "This AI verification is for preliminary information checking and does not "
    "replace professional or legal verification."
)


def calculate_similarity(str1: str, str2: str) -> float:
    """Calculates similarity percentage (0.0 to 100.0) between two strings."""
    if not str1 or not str2:
        return 0.0
    
    s1, s2 = str1.strip().lower(), str2.strip().lower()
    
    if s1 == s2:
        return 100.0

    if RAPIDFUZZ_AVAILABLE:
        return float(fuzz.token_sort_ratio(s1, s2))
    else:
        # Fallback simple word overlap
        words1 = set(s1.split())
        words2 = set(s2.split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return (len(intersection) / len(union)) * 100.0


def parse_numeric(val: Any) -> Optional[float]:
    """Helper to parse raw area/numbers from strings."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    match = re.search(r'([0-9\.,]+)', str(val))
    if match:
        clean_str = match.group(1).replace(',', '')
        try:
            return float(clean_str)
        except ValueError:
            return None
    return None


def verify_field(field_name: str, extracted_val: Optional[str], target_val: Optional[Any]) -> str:
    """
    Verifies a single field against a target property record value.
    Returns: 'match' | 'mismatch' | 'not_found'
    """
    if not extracted_val or not str(extracted_val).strip():
        return "not_found"

    if target_val is None or not str(target_val).strip():
        # Target record does not specify this property field to compare
        return "match"

    # Numeric comparison for area
    if field_name == "area":
        num_extracted = parse_numeric(extracted_val)
        num_target = parse_numeric(target_val)
        if num_extracted is not None and num_target is not None:
            # Check 5% tolerance
            diff = abs(num_extracted - num_target)
            if diff <= (num_target * 0.05) or diff <= 10.0:
                return "match"
            else:
                return "mismatch"

    # Fuzzy string matching for all text fields
    similarity = calculate_similarity(str(extracted_val), str(target_val))
    
    # Thresholds
    threshold = 70.0
    if field_name in ("property_id", "survey_number", "registration_number"):
        threshold = 80.0  # Stricter for exact registration & survey codes

    if similarity >= threshold:
        return "match"
    else:
        return "mismatch"


def verify_document_fields(
    extracted_fields: Dict[str, Optional[str]],
    target_property_record: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compares extracted document fields against listed property details.
    
    Target property record can include keys:
    - owner_name (or agent_name / title)
    - property_address (or address / city)
    - property_id (or id)
    - survey_number
    - area (or area_sqft)
    - document_date
    - registration_number
    """
    record = target_property_record or {}
    
    # Map target property record keys safely
    target_map = {
        "owner_name": record.get("owner_name") or record.get("agent_name") or record.get("title"),
        "property_address": record.get("property_address") or record.get("address"),
        "property_id": record.get("property_id") or record.get("id"),
        "survey_number": record.get("survey_number"),
        "area": record.get("area") or record.get("area_sqft"),
        "document_date": record.get("document_date"),
        "registration_number": record.get("registration_number"),
    }

    match_results: List[Dict[str, str]] = []
    has_mismatch = False
    has_match = False

    for field_name, extracted_val in extracted_fields.items():
        target_val = target_map.get(field_name)
        status = verify_field(field_name, extracted_val, target_val)
        
        match_results.append({
            "field": field_name,
            "status": status
        })
        
        if status == "mismatch":
            has_mismatch = True
        elif status == "match":
            has_match = True

    # Determine overall status
    if has_mismatch:
        overall_status = "mismatch"
    elif has_match:
        overall_status = "verified"
    else:
        overall_status = "pending"

    return {
        "extracted_fields": extracted_fields,
        "match_results": match_results,
        "overall_status": overall_status,
        "disclaimer": MANDATORY_DISCLAIMER
    }
