import pytest
from datetime import date
from app.services.cross_account import reconcile_cross_account_transfers

def test_hdfc_to_sbi_internal_transfer_confirmed():
    t_hdfc = {
        "id": "txn_hdfc_debit",
        "txn_date": date(2026, 6, 10),
        "debit": 50000.0,
        "credit": 0.0,
        "narration_raw": "TRANSFER TO SELF SBI ACCOUNT",
        "source_page_no": 1
    }
    t_sbi = {
        "id": "txn_sbi_credit",
        "txn_date": date(2026, 6, 10),
        "debit": 0.0,
        "credit": 50000.0,
        "narration_raw": "FUND TRANSFER FROM HDFC OWN A/C",
        "source_page_no": 1
    }

    stmts = {
        "stmt_hdfc": [t_hdfc],
        "stmt_sbi": [t_sbi]
    }

    confirmed, revs = reconcile_cross_account_transfers(stmts, customer_name="Ramesh Sharma")
    assert len(confirmed) == 1
    assert t_hdfc["is_internal_transfer"] is True
    assert t_sbi["is_internal_transfer"] is True
    assert t_hdfc["internal_match_id"] == t_sbi["internal_match_id"]
    assert len(revs) == 0

def test_third_party_not_internal():
    t1 = {
        "id": "t1",
        "txn_date": date(2026, 6, 12),
        "debit": 25000.0,
        "credit": 0.0,
        "narration_raw": "UPI/DR/12345/SUPPLIER PVT LTD/ICICI",
        "source_page_no": 1
    }
    t2 = {
        "id": "t2",
        "txn_date": date(2026, 6, 12),
        "debit": 0.0,
        "credit": 25000.0,
        "narration_raw": "UPI/CR/99999/CUSTOMER PAYMENT/SBI",
        "source_page_no": 1
    }

    stmts = {"stmt1": [t1], "stmt2": [t2]}
    confirmed, revs = reconcile_cross_account_transfers(stmts, customer_name="Ramesh Sharma")
    # Neither should be confirmed as internal transfer
    assert len(confirmed) == 0

def test_uncertain_gap_to_review():
    t1 = {
        "id": "t1",
        "txn_date": date(2026, 6, 1),
        "debit": 30000.0,
        "credit": 0.0,
        "narration_raw": "CHEQUE CLEARING",
        "source_page_no": 1
    }
    t2 = {
        "id": "t2",
        "txn_date": date(2026, 6, 3),  # 2 days gap, unclear narration
        "debit": 0.0,
        "credit": 30000.0,
        "narration_raw": "CHEQUE DEPOSIT",
        "source_page_no": 1
    }

    stmts = {"stmt1": [t1], "stmt2": [t2]}
    confirmed, revs = reconcile_cross_account_transfers(stmts, customer_name="Ramesh Sharma")
    assert len(confirmed) == 0
    assert len(revs) == 1
    assert revs[0]["issue_type"] == "CROSS_ACCOUNT_REVIEW"

