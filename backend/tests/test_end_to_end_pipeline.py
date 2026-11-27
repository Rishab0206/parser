import os
import io
import fitz
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.core.database import Base, get_db
from app.main import app
from app.models.models import Statement, Transaction, MonthlySummary, ReviewQueue, User
from app.core.security import get_current_user, CurrentUser, Role
from app.services.pdf_unlock import inspect_pdf_bytes


SQLALCHEMY_TEST_URL = "sqlite:///./test_e2e_bsi.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_current_user():
    return CurrentUser(user_id="test-admin-id", email="admin@test.com", name="Admin Test", role=Role.ADMIN)


@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    engine.dispose()
    if os.path.exists("./test_e2e_bsi.db"):
        os.remove("./test_e2e_bsi.db")


def build_bank_statement_pdf(
    pages_rows: list,
    password: str = None,
    bank_header: str = "KOTAK MAHINDRA BANK\nIFSC: KKBK0000123\nAccount No: 491800112233\nCustomer Name: Rajesh Sharma",
) -> bytes:
    """Builds a real digital PDF with drawn table borders so pdfplumber/PyMuPDF extract tables."""
    doc = fitz.open()
    for p_idx, rows in enumerate(pages_rows):
        page = doc.new_page(width=595, height=842)
        if p_idx == 0:
            page.insert_text((40, 40), bank_header, fontsize=10)
            y_start = 110
        else:
            page.insert_text((40, 40), f"Page {p_idx + 1} of {len(pages_rows)}", fontsize=9)
            y_start = 70

        col_x = [40, 110, 310, 390, 470, 555]
        row_h = 24
        for r_idx, row in enumerate(rows):
            y0 = y_start + r_idx * row_h
            y1 = y0 + row_h
            for c_idx in range(len(col_x) - 1):
                rect = fitz.Rect(col_x[c_idx], y0, col_x[c_idx + 1], y1)
                page.draw_rect(rect, color=(0, 0, 0), width=0.5)
                cell_text = str(row[c_idx]) if c_idx < len(row) else ""
                page.insert_text((col_x[c_idx] + 4, y0 + 15), cell_text, fontsize=8)

    if password:
        perm = int(fitz.PDF_PERM_ACCESSIBILITY | fitz.PDF_PERM_PRINT | fitz.PDF_PERM_COPY)
        pdf_bytes = doc.tobytes(
            garbage=4,
            deflate=True,
            encryption=fitz.PDF_ENCRYPT_AES_256,
            owner_pw="owner_master",
            user_pw=password,
            permissions=perm,
        )
    else:
        pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


SAMPLE_HEADER = ["Date", "Narration", "Debit", "Credit", "Balance"]
SAMPLE_ROWS_P1 = [
    SAMPLE_HEADER,
    ["01/10/2025", "OPENING BALANCE B/F", "-", "-", "50,000.00"],
    ["05/10/2025", "NEFT/CR/ACME TRADERS/INV01", "-", "25,000.00", "75,000.00"],
    ["10/10/2025", "NACH-DR-BAJAJ FINANCE EMI", "5,000.00", "-", "70,000.00"],
]
SAMPLE_ROWS_P2 = [
    SAMPLE_HEADER,
    ["15/10/2025", "UPI/CR/CLIENT PAYMENT", "-", "10,000.00", "80,000.00"],
    ["20/10/2025", "ATM CASH WITHDRAWAL", "2,000.00", "-", "78,000.00"],
]


def test_1_normal_unprotected_statement(client):
    pdf_bytes = build_bank_statement_pdf([SAMPLE_ROWS_P1])
    insp = client.post("/api/statements/inspect", files={"file": ("kotak.pdf", pdf_bytes, "application/pdf")})
    assert insp.status_code == 200
    assert insp.json()["is_encrypted"] is False
    assert insp.json()["is_valid"] is True

    up = client.post(
        "/api/statements/upload",
        files={"file": ("kotak.pdf", pdf_bytes, "application/pdf")},
        data={"application_id": "new", "account_type": "CURRENT"},
    )
    assert up.status_code == 200
    data = up.json()
    assert data["status"] in ["PARSED", "PARSED_WITH_WARNINGS"]

    st = client.get(f"/api/statements/{data['statement_id']}/status").json()
    assert st["bank_name"] == "Kotak Mahindra Bank"
    assert st["rows_parsed"] == 3
    assert st["opening_balance"] == 50000.0
    assert st["closing_balance"] == 70000.0
    assert st["reconciliation_status"] == "MATCHED"

    summary = client.get(f"/api/applications/{data['application_id']}/summary").json()
    assert summary["has_data"] is True
    assert summary["total_business_turnover"] == 25000.0


def test_2_3_4_password_protected_detect_wrong_and_correct_unlock(client):
    pdf_bytes = build_bank_statement_pdf([SAMPLE_ROWS_P1], password="KOTAK1990")

    # TEST 2: Inspect and upload without password -> PASSWORD_REQUIRED
    insp = client.post("/api/statements/inspect", files={"file": ("protected.pdf", pdf_bytes, "application/pdf")})
    assert insp.status_code == 200
    assert insp.json()["is_encrypted"] is True
    assert insp.json()["file_status"] == "PASSWORD_REQUIRED"

    up = client.post(
        "/api/statements/upload",
        files={"file": ("protected.pdf", pdf_bytes, "application/pdf")},
        data={"application_id": "new"},
    )
    assert up.status_code == 200
    up_data = up.json()
    assert up_data["status"] == "PASSWORD_REQUIRED"
    stmt_id = up_data["statement_id"]
    app_id = up_data["application_id"]

    # Summary must NOT show zero-value data while locked
    summary_locked = client.get(f"/api/applications/{app_id}/summary").json()
    assert summary_locked["has_data"] is False
    assert summary_locked["parsing_status"] == "PASSWORD_REQUIRED"

    # TEST 4: Wrong password -> 400 error, no zero-value dashboard
    bad = client.post(f"/api/statements/{stmt_id}/unlock", json={"password": "WRONG_PWD"})
    assert bad.status_code == 400
    assert "Incorrect PDF password" in bad.json()["message"]

    # TEST 3: Correct password -> unlocks & parses actual transactions
    good = client.post(f"/api/statements/{stmt_id}/unlock", json={"password": "KOTAK1990"})
    assert good.status_code == 200
    good_data = good.json()
    assert good_data["status"] in ["PARSED", "PARSED_WITH_WARNINGS"]
    assert good_data["rows_parsed"] == 3
    assert good_data["opening_balance"] == 50000.0
    assert good_data["closing_balance"] == 70000.0
    assert good_data["reconciliation_status"] == "MATCHED"

    summary_ok = client.get(f"/api/applications/{app_id}/summary").json()
    assert summary_ok["has_data"] is True
    assert summary_ok["total_business_turnover"] == 25000.0


def test_5_scanned_image_pdf_attempts_ocr_and_fails_cleanly_if_unreadable(client):
    # Create an image-only PDF (1 blank/noisy image)
    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 100, 100), False)
    pix.clear_with(255)
    page.insert_image(fitz.Rect(10, 10, 110, 110), stream=pix.tobytes("png"))
    scanned_bytes = doc.tobytes()
    doc.close()

    insp = inspect_pdf_bytes(scanned_bytes)
    assert insp["is_valid"] is True
    assert insp["is_scanned"] is True
    assert insp["classification"] == "SCANNED_PDF"

    up = client.post(
        "/api/statements/upload",
        files={"file": ("scanned.pdf", scanned_bytes, "application/pdf")},
        data={"application_id": "new"},
    )
    assert up.status_code == 200
    assert up.json()["status"] == "PARSING_FAILED"


def test_6_multipage_statement_extracts_all_pages(client):
    pdf_bytes = build_bank_statement_pdf([SAMPLE_ROWS_P1, SAMPLE_ROWS_P2])
    up = client.post(
        "/api/statements/upload",
        files={"file": ("multipage.pdf", pdf_bytes, "application/pdf")},
        data={"application_id": "new"},
    )
    assert up.status_code == 200
    data = up.json()
    st = client.get(f"/api/statements/{data['statement_id']}/status").json()
    assert st["page_count"] == 2
    assert st["rows_parsed"] == 5
    assert st["opening_balance"] == 50000.0
    assert st["closing_balance"] == 78000.0
    assert st["total_credits"] == 35000.0
    assert st["total_debits"] == 7000.0
    assert st["reconciliation_status"] == "MATCHED"


def test_7_corrupted_pdf_returns_invalid_file(client):
    bad_bytes = b"%PDF-1.4\nthis is corrupted garbage bytes!!!"
    insp = client.post("/api/statements/inspect", files={"file": ("bad.pdf", bad_bytes, "application/pdf")})
    assert insp.status_code == 200
    assert insp.json()["is_valid"] is False
    assert insp.json()["file_status"] == "INVALID_FILE"

    up = client.post(
        "/api/statements/upload",
        files={"file": ("bad.pdf", bad_bytes, "application/pdf")},
        data={"application_id": "new"},
    )
    assert up.status_code == 400
    assert up.json()["error_code"] == "INVALID_FILE"


def test_8_balance_mismatch_flags_warning(client):
    mismatch_rows = [
        SAMPLE_HEADER,
        ["01/10/2025", "OPENING BALANCE B/F", "-", "-", "50,000.00"],
        ["05/10/2025", "NEFT/CR/ACME", "-", "25,000.00", "99,999.00"],  # Wrong closing balance!
    ]
    pdf_bytes = build_bank_statement_pdf([mismatch_rows])
    up = client.post(
        "/api/statements/upload",
        files={"file": ("mismatch.pdf", pdf_bytes, "application/pdf")},
        data={"application_id": "new"},
    )
    assert up.status_code == 200
    data = up.json()
    assert data["status"] == "PARSED_WITH_WARNINGS"

    st = client.get(f"/api/statements/{data['statement_id']}/status").json()
    assert st["reconciliation_status"] == "MISMATCH"
    assert st["expected_closing_balance"] == 75000.0
    assert st["closing_balance"] == 99999.0
    assert st["reconciliation_diff"] == 24999.0


def test_9_empty_unreadable_statement_fails_not_zero(client):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((40, 40), "Just some random text with no bank statement table at all.")
    empty_pdf = doc.tobytes()
    doc.close()

    up = client.post(
        "/api/statements/upload",
        files={"file": ("empty_table.pdf", empty_pdf, "application/pdf")},
        data={"application_id": "new"},
    )
    assert up.status_code == 200
    data = up.json()
    assert data["status"] == "PARSING_FAILED"

    summary = client.get(f"/api/applications/{data['application_id']}/summary").json()
    assert summary["has_data"] is False
    assert summary["parsing_status"] == "PARSING_FAILED"


def test_10_excel_bank_statement_parses_successfully(client):
    import pandas as pd
    df = pd.DataFrame(
        [
            ["01/10/2025", "OPENING BALANCE B/F", 0.0, 0.0, 50000.0],
            ["05/10/2025", "NEFT/CR/ACME TRADERS/INV01", 0.0, 30000.0, 80000.0],
            ["10/10/2025", "NACH-DR-HDFC LOAN EMI", 10000.0, 0.0, 70000.0],
        ],
        columns=["Date", "Narration", "Debit", "Credit", "Balance"],
    )
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    xlsx_bytes = buf.getvalue()

    insp = client.post(
        "/api/statements/inspect",
        files={"file": ("statement.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert insp.status_code == 200
    assert insp.json()["is_valid"] is True
    assert insp.json()["is_encrypted"] is False

    up = client.post(
        "/api/statements/upload",
        files={"file": ("statement.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"application_id": "new", "account_type": "CURRENT"},
    )
    assert up.status_code == 200
    data = up.json()
    assert data["status"] in ["PARSED", "PARSED_WITH_WARNINGS"]

    st = client.get(f"/api/statements/{data['statement_id']}/status").json()
    assert st["rows_parsed"] == 3
    assert st["opening_balance"] == 50000.0
    assert st["closing_balance"] == 70000.0
    assert st["reconciliation_status"] == "MATCHED"
    assert st["processing_stage"] == "ANALYSIS_COMPLETED"
