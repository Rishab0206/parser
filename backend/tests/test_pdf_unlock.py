import pytest
import fitz
from app.services.pdf_unlock import unlock_pdf_in_memory, is_pdf_encrypted
from app.core.errors import PasswordRequiredException, InvalidPasswordException

def create_sample_pdf(password: str = None) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "HDFC BANK STATEMENT\nAccount: 50100123456789\nTurnover: 500000")
    if password:
        perm = int(
            fitz.PDF_PERM_ACCESSIBILITY
            | fitz.PDF_PERM_PRINT
            | fitz.PDF_PERM_COPY
            | fitz.PDF_PERM_ANNOTATE
        )
        pdf_bytes = doc.tobytes(
            garbage=4,
            deflate=True,
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw="owner123",
            user_pw=password,
            permissions=perm
        )
    else:
        pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes

def test_unencrypted_pdf_opens_cleanly():
    pdf_bytes = create_sample_pdf(password=None)
    assert not is_pdf_encrypted(pdf_bytes)
    doc, was_encrypted = unlock_pdf_in_memory(pdf_bytes)
    assert not was_encrypted
    assert len(doc) == 1
    doc.close()

def test_encrypted_pdf_requires_password():
    pdf_bytes = create_sample_pdf(password="secret123")
    assert is_pdf_encrypted(pdf_bytes)
    with pytest.raises(PasswordRequiredException):
        unlock_pdf_in_memory(pdf_bytes, password=None)

def test_encrypted_pdf_invalid_password_raises():
    pdf_bytes = create_sample_pdf(password="secret123")
    with pytest.raises(InvalidPasswordException):
        unlock_pdf_in_memory(pdf_bytes, password="wrongpassword")

def test_encrypted_pdf_unlocks_with_correct_password():
    pdf_bytes = create_sample_pdf(password="secret123")
    doc, was_encrypted = unlock_pdf_in_memory(pdf_bytes, password="secret123")
    assert was_encrypted
    text = doc[0].get_text()
    assert "HDFC BANK STATEMENT" in text
    doc.close()

def test_encrypted_pdf_auto_trims_and_case_normalizes():
    pdf_bytes = create_sample_pdf(password="PAN1234F")
    # Test whitespace trim
    doc1, _ = unlock_pdf_in_memory(pdf_bytes, password="  PAN1234F  ")
    assert doc1 is not None
    doc1.close()

    # Test lowercase input when password is uppercase
    doc2, _ = unlock_pdf_in_memory(pdf_bytes, password="pan1234f")
    assert doc2 is not None
    doc2.close()
