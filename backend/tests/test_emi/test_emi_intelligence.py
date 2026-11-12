import pytest
from datetime import date
from app.services.emi_detect import detect_emi_intelligence, is_excluded_recurring

def test_sip_and_rent_excluded():
    assert is_excluded_recurring("ACH D- NIPPON INDIA MUTUAL FUND SIP") is True
    assert is_excluded_recurring("UPI/DR/12345/OFFICE RENT PAYMENT/HDFC") is True
    assert is_excluded_recurring("ECS DR LIC PREMIUM PAYMENT") is True
    assert is_excluded_recurring("NACH-DR-BAJAJ FINANCE-12345") is False

def test_same_lender_two_separate_loans():
    # Bajaj loan 1: ₹12,500
    # Bajaj loan 2: ₹8,200
    txns = [
        {"txn_date": date(2026, 1, 5), "debit": 12500.0, "narration_raw": "NACH-DR-BAJAJ FINANCE-LOAN1"},
        {"txn_date": date(2026, 1, 10), "debit": 8200.0, "narration_raw": "NACH-DR-BAJAJ FINANCE-LOAN2"},
        {"txn_date": date(2026, 2, 5), "debit": 12500.0, "narration_raw": "NACH-DR-BAJAJ FINANCE-LOAN1"},
        {"txn_date": date(2026, 2, 10), "debit": 8200.0, "narration_raw": "NACH-DR-BAJAJ FINANCE-LOAN2"}
    ]

    confirmed, possible, attempts = detect_emi_intelligence(txns)
    # Must group into 2 distinct EMI records!
    assert len(confirmed) == 2
    amounts = sorted([r["amount"] for k, r in confirmed])
    assert amounts == [8200.0, 12500.0]

def test_weekly_frequency_emi():
    # Weekly micro-loan / NBFC EMI: ~7 days gap
    txns = [
        {"txn_date": date(2026, 3, 1), "debit": 2000.0, "narration_raw": "NACH-DR-CHOLA-WEEKLY"},
        {"txn_date": date(2026, 3, 8), "debit": 2000.0, "narration_raw": "NACH-DR-CHOLA-WEEKLY"},
        {"txn_date": date(2026, 3, 15), "debit": 2000.0, "narration_raw": "NACH-DR-CHOLA-WEEKLY"},
        {"txn_date": date(2026, 3, 22), "debit": 2000.0, "narration_raw": "NACH-DR-CHOLA-WEEKLY"}
    ]
    confirmed, possible, attempts = detect_emi_intelligence(txns)
    assert len(confirmed) == 1
    assert confirmed[0][1]["frequency"] == "WEEKLY"

def test_quarterly_frequency_emi():
    # Quarterly loan EMI: ~90 days gap
    txns = [
        {"txn_date": date(2026, 1, 15), "debit": 25000.0, "narration_raw": "ACH/TATA CAPITAL/QTR"},
        {"txn_date": date(2026, 4, 15), "debit": 25000.0, "narration_raw": "ACH/TATA CAPITAL/QTR"}
    ]
    confirmed, possible, attempts = detect_emi_intelligence(txns)
    assert len(confirmed) == 1
    assert confirmed[0][1]["frequency"] == "QUARTERLY"

def test_probable_vs_confirmed_classification():
    # Probable: recurring identical amount, gap 30 days, but NO NACH/EMI keyword
    txns_probable = [
        {"txn_date": date(2026, 1, 10), "debit": 14000.0, "narration_raw": "NEFT TO ABC FINTECH", "counterparty": "ABC FINTECH"},
        {"txn_date": date(2026, 2, 10), "debit": 14000.0, "narration_raw": "NEFT TO ABC FINTECH", "counterparty": "ABC FINTECH"}
    ]
    confirmed, possible, attempts = detect_emi_intelligence(txns_probable)
    assert len(confirmed) == 1
    assert confirmed[0][1]["lender_confidence"] == "PROBABLE"

