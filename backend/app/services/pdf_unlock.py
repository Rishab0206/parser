import fitz  # PyMuPDF
from typing import Optional, Tuple
from app.core.errors import PasswordRequiredException, InvalidPasswordException
from app.core.logging import logger

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
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Could not open document as PDF: {str(e)}")

    if not doc.is_encrypted:
        return doc, False

    logger.info("PDF is encrypted, attempting unlock with provided password: [REDACTED]")

    if not password or not str(password).strip():
        doc.close()
        raise PasswordRequiredException("PDF is password protected. Please provide a password.")

    raw_pwd = str(password)
    clean_pwd = raw_pwd.strip()

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

    # Wipe local variable reference from memory immediately
    raw_pwd = None
    clean_pwd = None
    del raw_pwd
    del clean_pwd

    if not unlocked:
        doc.close()
        raise InvalidPasswordException("Incorrect PDF password. Please verify your password and try again.")

    return doc, True
