import pytest
from app.core.encryption import mask_account_number, mask_phone_number, encrypt_string, decrypt_string
from app.core.logging import RedactingFormatter
import logging

def test_account_and_phone_masking():
    assert mask_account_number("5010023456786693") == "XXXX6693"
    assert mask_account_number("1234") == "XXXX1234"
    assert mask_phone_number("9876543210") == "98XXX X3210"

def test_fernet_encryption_roundtrip():
    secret = "50100987654321"
    encrypted = encrypt_string(secret)
    assert encrypted != secret
    decrypted = decrypt_string(encrypted)
    assert decrypted == secret

def test_logger_redacts_passwords():
    formatter = RedactingFormatter(fmt="%(message)s")
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg="Processing with password: SuperSecretPassword123! in request",
        args=(), exc_info=None
    )
    formatted = formatter.format(record)
    assert "SuperSecretPassword123!" not in formatted
    assert "[REDACTED]" in formatted

