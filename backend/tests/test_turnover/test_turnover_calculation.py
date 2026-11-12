import pytest
from datetime import date
from app.services.turnover_calc import calculate_monthly_turnover_and_flows

def test_business_turnover_vs_non_business_and_internal():
    txns = [
        # Business receipts: ₹1,00,000 + ₹50,000 = ₹1,50,000
        {"txn_date": date(2026, 4, 2), "credit": 100000.0, "debit": 0.0, "category": "BUSINESS_RECEIPT", "is_internal_transfer": False},
        {"txn_date": date(2026, 4, 8), "credit": 50000.0, "debit": 0.0, "category": "BUSINESS_RECEIPT", "is_internal_transfer": False},
        # Loan disbursal (non-business): ₹2,00,000
        {"txn_date": date(2026, 4, 10), "credit": 200000.0, "debit": 0.0, "category": "LOAN_DISBURSAL", "is_internal_transfer": False},
        # Internal transfer: ₹30,000
        {"txn_date": date(2026, 4, 15), "credit": 30000.0, "debit": 0.0, "category": "INTERNAL_TRANSFER", "is_internal_transfer": True},
        # Business debits: ₹80,000
        {"txn_date": date(2026, 4, 20), "credit": 0.0, "debit": 80000.0, "category": "GENERAL_EXPENSE", "is_internal_transfer": False}
    ]

    # EMI attempt: 1 success ₹15,000, 1 returned bounce ₹10,000
    emi_attempts = [
        {"attempt_date": date(2026, 4, 5), "amount": 15000.0, "status": "SUCCESS"},
        {"attempt_date": date(2026, 4, 12), "amount": 10000.0, "status": "RETURNED"}
    ]

    results = calculate_monthly_turnover_and_flows(txns, emi_attempts)
    assert len(results) == 1
    r = results[0]

    # Gross credit = 100000 + 50000 + 200000 + 30000 = 380000
    assert r["gross_credit"] == 380000.0
    # Business turnover = 150000
    assert r["business_turnover"] == 150000.0
    # Non-business credit = 200000
    assert r["non_business_credit"] == 200000.0
    # Internal transfer excluded = 30000
    assert r["internal_transfer_credit_excluded"] == 30000.0
    # Total debit = 80000
    assert r["total_debit"] == 80000.0
    # Net flow = 150000 - 80000 = 70000
    assert r["net_flow"] == 70000.0

    # EMI burden must count ONLY SUCCESSFUL attempts: ₹15,000
    assert r["emi_burden"] == 15000.0
    assert r["emi_bounce_count"] == 1

    # EMI-to-Turnover Ratio: 15,000 / 150,000 * 100 = 10.0%
    assert r["emi_to_turnover_ratio"] == 10.0

