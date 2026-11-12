import pytest
from datetime import date
from app.services.abb_calc import compute_monthly_abb_metrics

def test_abb_calculation_and_low_balance():
    # 3 transactions spanning a month with carry-forward
    txns = [
        {"txn_date": date(2026, 4, 1), "balance": 10000.0, "debit": 0.0, "credit": 0.0},
        {"txn_date": date(2026, 4, 10), "balance": 3000.0, "debit": 7000.0, "credit": 0.0},
        {"txn_date": date(2026, 4, 20), "balance": -2000.0, "debit": 5000.0, "credit": 0.0},
        {"txn_date": date(2026, 4, 25), "balance": 15000.0, "debit": 0.0, "credit": 17000.0}
    ]

    metrics = compute_monthly_abb_metrics(txns, account_type="SAVINGS")
    assert len(metrics) == 1
    m = metrics[0]
    assert m["month"] == "2026-04"
    assert m["min_balance"] == -2000.0
    assert m["min_balance_date"] == date(2026, 4, 20)
    assert m["month_end_balance"] == 15000.0
    # Negative days from 20th to 24th (5 days: 20, 21, 22, 23, 24)
    assert m["negative_days"] == 5
    # Days below 5000: 10th to 19th (10 days)
    assert m["days_below_5000"] == 10

def test_partial_month_flag():
    # Starts on April 15
    txns = [
        {"txn_date": date(2026, 4, 15), "balance": 50000.0, "debit": 0.0, "credit": 0.0},
        {"txn_date": date(2026, 4, 30), "balance": 50000.0, "debit": 0.0, "credit": 0.0}
    ]
    metrics = compute_monthly_abb_metrics(txns, account_type="SAVINGS")
    assert len(metrics) == 1
    assert metrics[0]["is_partial"] is True
    assert metrics[0]["available_days"] == 16

def test_od_account_utilization():
    # OD account with limit 1,00,000
    txns = [
        {"txn_date": date(2026, 5, 1), "balance": -50000.0, "debit": 50000.0, "credit": 0.0},
        {"txn_date": date(2026, 5, 31), "balance": -50000.0, "debit": 0.0, "credit": 0.0}
    ]
    metrics = compute_monthly_abb_metrics(txns, account_type="OD", sanctioned_limit=100000.0)
    assert len(metrics) == 1
    assert metrics[0]["account_type"] == "OD"
    # Utilization should be 50%
    assert metrics[0]["utilization_pct"] == 50.0

