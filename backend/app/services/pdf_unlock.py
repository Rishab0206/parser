import fitz  # PyMuPDF
from typing import Optional, Tuple, Dict, Any
from app.core.errors import (
    PasswordRequiredException,
    InvalidPasswordException,
    CorruptedPdfException,
    UnsupportedEncryptionException,
)
from app.core.logging import logger

def inspect_pdf_bytes(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Inspects a PDF byte stream without modifying or persisting passwords.
    Distinguishes:
      A. Normal, unencrypted PDF
      B. Password-protected PDF
      C. Corrupted or invalid PDF
      D. Scanned/image-based PDF
      E. PDF that opens but contains no extractable text
    """
    if not pdf_bytes or len(pdf_bytes) < 10:
        return {
            "is_valid": False,
            "is_encrypted": False,
            "is_scanned": False,
            "has_extractable_text": False,
            "page_count": 0,
            "file_status": "INVALID_FILE",
            "classification": "CORRUPTED_PDF",
            "message": "Invalid or empty PDF file."
        }

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        logger.warning(f"PDF inspection failed (corrupted/invalid): {e}")
        return {
            "is_valid": False,
            "is_encrypted": False,
            "is_scanned": False,
            "has_extractable_text": False,
            "page_count": 0,
            "file_status": "INVALID_FILE",
            "classification": "CORRUPTED_PDF",
            "message": "Invalid or corrupted PDF file. Unable to open document."
        }

    try:
        is_encrypted = bool(doc.is_encrypted)
        page_count = len(doc)

        if is_encrypted:
            return {
                "is_valid": True,
                "is_encrypted": True,
                "is_scanned": False,
                "has_extractable_text": False,
                "page_count": page_count,
                "file_status": "PASSWORD_REQUIRED",
                "classification": "PASSWORD_PROTECTED",
                "message": "PDF is password protected. Please enter the PDF password to unlock and parse."
            }

        if page_count == 0:
            return {
                "is_valid": False,
                "is_encrypted": False,
                "is_scanned": False,
                "has_extractable_text": False,
                "page_count": 0,
                "file_status": "INVALID_FILE",
                "classification": "CORRUPTED_PDF",
                "message": "PDF contains zero pages."
            }

        # Check text vs image/scanned content
        total_chars = 0
        has_images = False
        for i in range(min(page_count, 5)):
            page = doc[i]
            txt = page.get_text("text") or ""
            total_chars += len(txt.strip())
            if page.get_images(full=False):
                has_images = True

        avg_chars = total_chars / max(min(page_count, 5), 1)
        has_extractable_text = total_chars >= 50 and avg_chars >= 100
        is_scanned = (not has_extractable_text) and has_images

        if is_scanned:
            classification = "SCANNED_PDF"
            msg = "Scanned/image-based PDF detected. OCR extraction will be used automatically."
        elif not has_extractable_text:
            classification = "NO_EXTRACTABLE_TEXT"
            msg = "PDF opened, but contains minimal/no extractable text. OCR fallback will be attempted."
        else:
            classification = "NORMAL_PDF"
            msg = "No password required. Ready to parse."

        return {
            "is_valid": True,
            "is_encrypted": False,
            "is_scanned": is_scanned,
            "has_extractable_text": has_extractable_text,
            "page_count": page_count,
            "file_status": "FILE_UPLOADED",
            "classification": classification,
            "message": msg
        }
    finally:
        doc.close()

def is_pdf_encrypted(pdf_bytes: bytes) -> bool:
    """Checks whether a PDF byte stream is password-protected."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        encrypted = bool(doc.is_encrypted)
        doc.close()
        return encrypted
    except Exception:
        return False

def unlock_pdf_in_memory(pdf_bytes: bytes, password: Optional[str] = None) -> Tuple[fitz.Document, bool]:
    """
    Unlocks password-protected PDF entirely in memory.
    NEVER stores password in database, logs, or disk.
    Immediately clears password from variable scope.
    Supports intelligent auto-trim and case normalization for Indian bank statements.
    """
    if not pdf_bytes or len(pdf_bytes) < 10:
        raise CorruptedPdfException("Invalid or empty PDF file.")

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise CorruptedPdfException(f"Could not open document as PDF (file may be corrupted): {str(e)}")

    if not doc.is_encrypted:
        return doc, False

    logger.info("PDF is encrypted, attempting unlock with provided password: [REDACTED]")

    if not password or not str(password).strip():
        doc.close()
        raise PasswordRequiredException("PDF is password protected. Please provide a password.")

    raw_pwd = str(password)
    clean_pwd = raw_pwd.strip()

    try:
        # Attempt 1: Exact match as provided
        unlocked = doc.authenticate(raw_pwd)

        # Attempt 2: Trimmed whitespace
        if not unlocked and clean_pwd != raw_pwd:
            unlocked = doc.authenticate(clean_pwd)

        # Attempt 3: Uppercase variant (common for PAN + DOB)
        if not unlocked and clean_pwd.upper() != clean_pwd:
            unlocked = doc.authenticate(clean_pwd.upper())

        # Attempt 4: Lowercase variant
        if not unlocked and clean_pwd.lower() != clean_pwd:
            unlocked = doc.authenticate(clean_pwd.lower())
    except Exception as auth_err:
        doc.close()
        raise UnsupportedEncryptionException(f"Unsupported PDF encryption method: {str(auth_err)}")
    finally:
        # Wipe local variable reference from memory immediately
        raw_pwd = None
        clean_pwd = None
        del raw_pwd
        del clean_pwd

    if not unlocked:
        doc.close()
        raise InvalidPasswordException("Incorrect PDF password. Please enter the correct password and try again.")

    return doc, True
