import os
import io
from PIL import Image
from app.core.logging import logger
from app.core.config import settings

def perform_ocr_on_image(image_bytes: bytes) -> str:
    """
    Performs OCR using Tesseract (`tesseract-ocr`) for scanned or low-quality bank statements.
    In production (e.g. Render 512MB containers), skips heavy PyTorch/EasyOCR fallback unless
    ENABLE_EASYOCR=true to prevent Out-Of-Memory (502) crashes.
    """
    try:
        import pytesseract
        image = Image.open(io.BytesIO(image_bytes)).convert("L")
        text = pytesseract.image_to_string(image, lang="eng")
        if text and len(text.strip()) > 0:
            return text
    except Exception as e:
        logger.warning(f"pytesseract OCR error: {e}")

    # Optional EasyOCR fallback (disabled by default in production to avoid 512MB OOM)
    enable_easyocr = os.environ.get("ENABLE_EASYOCR", "").lower() == "true"
    if settings.ENVIRONMENT != "production" or enable_easyocr:
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
