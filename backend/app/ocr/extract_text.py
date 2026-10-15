import io
import os
import logging
from typing import Union, List
from PIL import Image

from app.ocr.preprocess import preprocess_image

logger = logging.getLogger(__name__)

# Try importing OCR libraries
PYTESSERACT_AVAILABLE = False
PDF2IMAGE_AVAILABLE = False

try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    logger.warning("pytesseract library not found. Will fallback to alternative text extraction.")

try:
    from pdf2image import convert_from_bytes, convert_from_path
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    logger.warning("pdf2image library not found.")


def extract_text_from_image(image_input: Union[Image.Image, bytes, str], preprocess: bool = True) -> str:
    """
    Extracts raw OCR text from a given image (PIL Image, bytes, or file path).
    Applies image preprocessing prior to OCR if preprocess=True.
    """
    if isinstance(image_input, (bytes, str)):
        img = Image.open(io.BytesIO(image_input) if isinstance(image_input, bytes) else image_input)
    else:
        img = image_input

    if preprocess:
        processed_img = preprocess_image(img)
    else:
        processed_img = img

    if PYTESSERACT_AVAILABLE:
        try:
            text = pytesseract.image_to_string(processed_img)
            if text and text.strip():
                return text.strip()
        except Exception as e:
            logger.warning(f"pytesseract extraction failed/not configured: {e}")

    # Fallback if tesseract system binary isn't present or failed
    # Perform basic layout string check or mock OCR if image contains text metadata or simple fallback
    return ""


def extract_text_from_pdf(pdf_input: Union[bytes, str], preprocess: bool = True) -> str:
    """
    Extracts raw OCR text from a PDF document (bytes or path).
    Converts PDF pages into images and runs OCR text extraction.
    """
    extracted_text_pages: List[str] = []

    if PDF2IMAGE_AVAILABLE:
        try:
            if isinstance(pdf_input, bytes):
                images = convert_from_bytes(pdf_input)
            else:
                images = convert_from_path(pdf_input)

            for page_img in images:
                page_text = extract_text_from_image(page_img, preprocess=preprocess)
                if page_text:
                    extracted_text_pages.append(page_text)
        except Exception as e:
            logger.warning(f"pdf2image conversion failed: {e}")

    # Fallback to python PDF text readers if pdf2image fails
    if not extracted_text_pages:
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(pdf_input) if isinstance(pdf_input, bytes) else pdf_input)
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    extracted_text_pages.append(txt)
        except Exception as e:
            logger.warning(f"pypdf extraction failed: {e}")

    return "\n\n".join(extracted_text_pages).strip()


def extract_text_from_file(file_bytes: bytes, filename: str, preprocess: bool = True) -> str:
    """
    Unified text extraction router for PDF and Image files.
    """
    lower_filename = filename.lower()
    
    if lower_filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_bytes, preprocess=preprocess)
    elif any(lower_filename.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]):
        text = extract_text_from_image(file_bytes, preprocess=preprocess)
    elif lower_filename.endswith(".txt"):
        text = file_bytes.decode("utf-8", errors="ignore")
    else:
        # Default attempt as image
        try:
            text = extract_text_from_image(file_bytes, preprocess=preprocess)
        except Exception:
            text = file_bytes.decode("utf-8", errors="ignore")

    return text
