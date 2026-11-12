import pytest
from datetime import date
from app.services.return_match import reconcile_returns_and_charges

def test_return_reconciliation_with_separate_charge():
    # Attempt: EMI debit ₹12,500 on 5th
    # Return credit: ₹12,500 on 6th
    # Bounce charge debit: ₹590 on 6th
    attempt_txn = {
        "id": "txn_emi_1",
        "txn_date": date(2026, 4, 5),
        "debit": 12500.0,
        "credit": 0.0,
        "narration_raw": "NACH-DR-BAJAJ FINANCE-12345",
        "source_page_no": 1
    }
    return_txn = {
        "id": "txn_ret_1",
        "txn_date": date(2026, 4, 6),
        "debit": 0.0,
        "credit": 12500.0,
        "narration_raw": "NACH RETURN-INSUFFICIENT FUNDS-BAJAJ",
        "source_page_no": 1
    }
    charge_txn = {
        "id": "txn_chg_1",
        "txn_date": date(2026, 4, 6),
        "debit": 590.0,
        "credit": 0.0,
        "narration_raw": "NACH RTN CHG / BOUNCE PENALTY",
        "source_page_no": 1
    }

    attempts = [{
        "id": "att_1",
        "transaction_id": "txn_emi_1",
        "attempt_date": date(2026, 4, 5),
        "amount": 12500.0,
        "status": "SUCCESS",
        "transaction": attempt_txn
    }]

    all_txns = [attempt_txn, return_txn, charge_txn]
    returns, revs = reconcile_returns_and_charges(all_txns, attempts)

    assert len(returns) == 1
    rec = returns[0]
    assert rec["return_amount"] == 12500.0
    assert rec["return_charge_amount"] == 590.0
    assert rec["charge_txn_id"] == "txn_chg_1"
    assert rec["reason"] == "INSUFFICIENT_FUNDS"
    assert attempts[0]["status"] == "RETURNED"

def test_ambiguous_same_amount_match_to_review():
    # Two identical EMI debits on same day, one return
    t1 = {"id": "t1", "txn_date": date(2026, 5, 2), "debit": 5000.0, "credit": 0.0, "narration_raw": "NACH DR LENDER A", "source_page_no": 1}
    t2 = {"id": "t2", "txn_date": date(2026, 5, 2), "debit": 5000.0, "credit": 0.0, "narration_raw": "NACH DR LENDER B", "source_page_no": 1}
    ret = {"id": "ret", "txn_date": date(2026, 5, 4), "debit": 0.0, "credit": 5000.0, "narration_raw": "ECS RETURN UNPAID", "source_page_no": 1}

    attempts = [
        {"id": "a1", "transaction_id": "t1", "attempt_date": date(2026, 5, 2), "amount": 5000.0, "status": "SUCCESS", "transaction": t1},
        {"id": "a2", "transaction_id": "t2", "attempt_date": date(2026, 5, 2), "amount": 5000.0, "status": "SUCCESS", "transaction": t2}
    ]

    returns, revs = reconcile_returns_and_charges([t1, t2, ret], attempts)
    # Ambiguous match must go to Review Queue
    assert len(revs) == 1
    assert revs[0]["issue_type"] == "AMBIGUOUS_RETURN_MATCH"

