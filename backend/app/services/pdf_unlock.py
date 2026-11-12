import fitz  # PyMuPDF
from typing import Optional, Tuple
from app.core.errors import PasswordRequiredException, InvalidPasswordException
from app.core.logging import logger

def unlock_pdf_in_memory(pdf_bytes: bytes, password: Optional[str] = None) -> Tuple[fitz.Document, bool]:
    """
    Unlocks password-protected PDF entirely in memory.
    NEVER stores password in database, logs, or disk.
    Immediately clears password from variable scope.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as e:
        raise ValueError(f"Could not open document as PDF: {str(e)}")

    if not doc.is_encrypted:
        return doc, False

    logger.info("PDF is encrypted, attempting unlock with provided password: [REDACTED]")

    if not password:
        doc.close()
        raise PasswordRequiredException("PDF is password protected. Please provide a password.")

    pwd_str = str(password)
    unlocked = doc.authenticate(pwd_str)
    # Wipe local variable reference
    pwd_str = None
    del pwd_str

    if not unlocked:
        doc.close()
        raise InvalidPasswordException("Incorrect PDF password")

    return doc, True

