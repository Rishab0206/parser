import base64
from cryptography.fernet import Fernet
from app.core.config import settings

def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY
    if isinstance(key, str):
        key = key.encode("utf-8")
    return Fernet(key)

def encrypt_data(data: bytes) -> bytes:
    """Encrypt raw bytes at rest with AES-256 Fernet."""
    f = _get_fernet()
    return f.encrypt(data)

def decrypt_data(token: bytes) -> bytes:
    """Decrypt raw bytes from storage."""
    f = _get_fernet()
    return f.decrypt(token)

def encrypt_string(text: str) -> str:
    """Encrypt sensitive string (e.g. full bank account number)."""
    if not text:
        return ""
    token = _get_fernet().encrypt(text.encode("utf-8"))
    return token.decode("utf-8")

def decrypt_string(token_str: str) -> str:
    """Decrypt encrypted string to plaintext."""
    if not token_str:
        return ""
    decrypted = _get_fernet().decrypt(token_str.encode("utf-8"))
    return decrypted.decode("utf-8")

def mask_account_number(account_no: str) -> str:
    """Mask account number to XXXX + last 4 digits (e.g. XXXX6693)."""
    if not account_no:
        return "XXXX----"
    clean = str(account_no).strip()
    if len(clean) <= 4:
        return "XXXX" + clean
    return "XXXX" + clean[-4:]

def mask_phone_number(phone: str) -> str:
    """Mask phone number e.g. 98XXX XXXXX."""
    if not phone:
        return ""
    clean = "".join([c for c in phone if c.isdigit()])
    if len(clean) >= 10:
        return f"{clean[:2]}XXX X{clean[-4:]}"
    return "XXXXXXXXXX"

