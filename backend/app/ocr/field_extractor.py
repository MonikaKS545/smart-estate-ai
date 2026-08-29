import re
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Try importing spacy for advanced NLP extraction if installed
SPACY_AVAILABLE = False
nlp_model = None

try:
    import spacy
    try:
        nlp_model = spacy.load("en_core_web_sm")
        SPACY_AVAILABLE = True
    except Exception:
        logger.info("spaCy en_core_web_sm model not loaded. Using enhanced regex and NLP heuristics.")
except ImportError:
    logger.info("spaCy library not installed. Using regex heuristics for field extraction.")


def extract_survey_number(text: str) -> Optional[str]:
    """Extracts survey number (e.g., Sy No 124/2A, Survey No. 45/1, Sy. 89)."""
    patterns = [
        r'(?:Survey\s*(?:Number|Num|No|\.)?|Sy\s*\.?\s*No\.?|Plot\s*No\.?)\s*[:\-]?\s*(?:Sy\s*\.?\s*No\.?\s*)?([0-9]+[A-Za-z0-9\/\-]*)',
        r'\b(?:Sy|Sy\.?|Survey)\s*#?\s*([0-9]+[A-Za-z0-9\/\-]*)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if val and not val.lower().startswith('ber'):
                return val
    return None


def extract_registration_number(text: str) -> Optional[str]:
    """Extracts registration / deed / document number."""
    patterns = [
        r'(?:Registration\s*(?:Number|Num|No|\.)?|Doc\.?\s*Reg\.?\s*No\.?|Deed\s*No\.?|Doc\s*No\.?|Reg\s*#)\s*[:\-]?\s*([A-Za-z0-9\/\-]+)',
        r'\b(REG\/[0-9]{4}\/[0-9]+)\b',
        r'\b(DOC-[0-9]{4,8})\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            if val and not val.lower().startswith('ber'):
                return val
    return None


def extract_property_id(text: str) -> Optional[str]:
    """Extracts property ID / PID / Khata No."""
    patterns = [
        r'(?:Property\s*ID|PID|Property\s*Code|Khata\s*No\.?)\s*[:\-]?\s*([A-Za-z0-9\/\-]+)',
        r'\b(PROP-[0-9]{3,8})\b',
        r'\b(PID-[0-9]{3,8})\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_area(text: str) -> Optional[str]:
    """Extracts property area (e.g., 1200 sq ft, 1500 sqft, 250 Sq. Meters)."""
    patterns = [
        r'(?:Area|Extent|Built\s*up\s*area|Carpet\s*area|Plot\s*area)\s*[:\-\/]?\s*([0-9\.,]+\s*(?:sq\.?\s*ft\.?|sqft|sq\.?\s*m\.?|sqm|square\s*feet|acres|cents)[^\n,]*)',
        r'\b([0-9\.,]+\s*(?:sq\.?\s*ft\.?|sqft|square\s*feet))\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_document_date(text: str) -> Optional[str]:
    """Extracts document execution or registration date."""
    patterns = [
        r'(?:Date|Executed\s*on|Dated|Registration\s*Date)\s*[:\-]?\s*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})',
        r'(?:Date|Executed\s*on|Dated)\s*[:\-]?\s*([0-9]{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+[0-9]{4})',
        r'\b([0-9]{4}[\/\-][0-9]{2}[\/\-][0-9]{2})\b',
        r'\b([0-9]{1,2}[\/\-][0-9]{1,2}[\/\-][0-9]{4})\b',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_owner_name(text: str) -> Optional[str]:
    """Extracts owner / purchaser / vendor / claimant name."""
    patterns = [
        r'(?:Purchaser\s*\/\s*Owner\s*Name|Owner\s*Name|Owner|Purchaser|Buyer|Claimant|Proprietor|Name\s*of\s*Owner)\s*[:\-]?\s*([A-Za-z\s\.]+)(?=\n|,|Address|Survey|Date|\d)',
        r'(?:Mr\.|Mrs\.|Ms\.|Shri|Smt\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            name = re.sub(r'\s+(?:Address|Survey|Phone|Date|Property).*$', '', name, flags=re.IGNORECASE).strip()
            if len(name.split()) >= 1 and len(name) > 2:
                return name

    if SPACY_AVAILABLE and nlp_model:
        doc = nlp_model(text)
        for ent in doc.ents:
            if ent.label_ == "PERSON" and len(ent.text.split()) <= 4:
                return ent.text.strip()

    return None


def extract_property_address(text: str) -> Optional[str]:
    """Extracts property address or location details."""
    patterns = [
        r'(?:Property\s*Address|Address|Location|Situated\s*at|Premises)\s*[:\-]?\s*([^\n]+(?:\n[^\n]+){0,2})',
        r'(?:Plot|Flat|House|Door)\s*No\.?\s*[^\n,]+,\s*[^\n]+',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            addr = match.group(1).strip()
            addr = re.split(r'(?:Survey|Date|Registration|Area|Owner):', addr, flags=re.IGNORECASE)[0].strip()
            return addr
    return None


def extract_fields(raw_text: str) -> Dict[str, Optional[str]]:
    """
    Parses raw text extracted from a property document and extracts all 7 required fields:
    1. owner_name
    2. property_address
    3. property_id
    4. survey_number
    5. area
    6. document_date
    7. registration_number
    """
    if not raw_text:
        return {
            "owner_name": None,
            "property_address": None,
            "property_id": None,
            "survey_number": None,
            "area": None,
            "document_date": None,
            "registration_number": None,
        }

    return {
        "owner_name": extract_owner_name(raw_text),
        "property_address": extract_property_address(raw_text),
        "property_id": extract_property_id(raw_text),
        "survey_number": extract_survey_number(raw_text),
        "area": extract_area(raw_text),
        "document_date": extract_document_date(raw_text),
        "registration_number": extract_registration_number(raw_text),
    }
