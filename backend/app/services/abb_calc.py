import calendar
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, timedelta
from collections import defaultdict

def calculate_daily_eod_balances(
    transactions: List[Dict[str, Any]]
) -> Dict[str, Dict[date, float]]:
    """
    Computes daily End-of-Day (EOD) balance per month with carry-forward for non-transaction days.
    Returns: { "YYYY-MM": { date_obj: eod_balance, ... } }
    """
    if not transactions:
        return {}

    sorted_txns = sorted(transactions, key=lambda x: (x["txn_date"], x.get("id", "")))
    first_date = sorted_txns[0]["txn_date"]
    last_date = sorted_txns[-1]["txn_date"]

    # Map actual day to final transaction balance on that day
    day_last_balance = {}
    for t in sorted_txns:
        day_last_balance[t["txn_date"]] = float(t["balance"])

    # Carry forward day by day
    monthly_daily_balances = defaultdict(dict)
    curr_date = first_date
    running_balance = float(sorted_txns[0]["balance"])

    while curr_date <= last_date:
        if curr_date in day_last_balance:
            running_balance = day_last_balance[curr_date]

        month_key = curr_date.strftime("%Y-%m")
        monthly_daily_balances[month_key][curr_date] = running_balance
        curr_date += timedelta(days=1)

    return monthly_daily_balances

def compute_monthly_abb_metrics(
    transactions: List[Dict[str, Any]],
    account_type: str = "SAVINGS",
    sanctioned_limit: Optional[float] = None
) -> List[Dict[str, Any]]:
    """
    Computes ABB, Min, Max, Month-end balance, negative days, days below 5000/10000.
    Handles OD/CC utilization vs standard savings/current ABB.
    """
    daily_balances_by_month = calculate_daily_eod_balances(transactions)
    monthly_results = []

    for month_str in sorted(daily_balances_by_month.keys()):
        days_dict = daily_balances_by_month[month_str]
        year, month = map(int, month_str.split("-"))
        total_days_in_month = calendar.monthrange(year, month)[1]
        available_days = len(days_dict)
        is_partial = available_days < total_days_in_month

        balances = list(days_dict.values())
        if not balances:
            continue

        # Standard ABB formula: sum(daily EOD) / count(days)
        abb_value = sum(balances) / available_days
        min_balance = min(balances)
        max_balance = max(balances)

        # Date of min balance
        min_balance_date = [d for d, b in days_dict.items() if b == min_balance][0]

        # Month-end balance: balance on the latest day available in that month
        latest_day = max(days_dict.keys())
        month_end_balance = days_dict[latest_day]

        # Negative days and low-balance counts
        negative_days = sum(1 for b in balances if b < 0.0)
        days_below_5000 = sum(1 for b in balances if 0.0 <= b < 5000.0)
        days_below_10000 = sum(1 for b in balances if 0.0 <= b < 10000.0)

        # Handle OD / CC special calculations
        utilization_pct = None
        od_note = None
        if account_type in ["OD", "CC"]:
            if sanctioned_limit and sanctioned_limit > 0:
                # Utilized = abs(min(0, b)) or utilized balance
                daily_util = [abs(min(0.0, b)) for b in balances]
                utilization_pct = (sum(daily_util) / available_days) / sanctioned_limit * 100.0
            else:
                od_note = "Limit not in statement — utilization N/A"

        monthly_results.append({
            "month": month_str,
            "abb": round(abb_value, 2),
            "min_balance": round(min_balance, 2),
            "max_balance": round(max_balance, 2),
            "min_balance_date": min_balance_date,
            "month_end_balance": round(month_end_balance, 2),
            "negative_days": negative_days,
            "days_below_5000": days_below_5000,
            "days_below_10000": days_below_10000,
            "is_partial": is_partial,
            "total_days": total_days_in_month,
            "available_days": available_days,
            "account_type": account_type,
            "utilization_pct": round(utilization_pct, 2) if utilization_pct is not None else None,
            "od_note": od_note
        })

    return monthly_results

