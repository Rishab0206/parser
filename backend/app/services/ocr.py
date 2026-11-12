from typing import Optional, List
import io
from PIL import Image
from app.core.logging import logger

def perform_ocr_on_image(image_bytes: bytes) -> str:
    """
    Performs OCR using Tesseract with EasyOCR fallback for scanned or low-quality bank statements.
    """
    try:
        import pytesseract
        image = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(image, lang="eng")
        if len(text.strip()) > 30:
            return text
    except Exception as e:
        logger.warning(f"pytesseract OCR error, trying fallback: {e}")

    # Fallback to EasyOCR if available
    try:
        import easyocr
        import numpy as np
        reader = easyocr.Reader(['en'], gpu=False)
        img_np = np.array(Image.open(io.BytesIO(image_bytes)))
        results = reader.readtext(img_np, detail=0)
        return "\n".join(results)
    except Exception as e:
        logger.warning(f"EasyOCR fallback error: {e}")
        return ""

