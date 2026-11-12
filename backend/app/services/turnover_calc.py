from typing import List, Dict, Any, Tuple
from collections import defaultdict
from datetime import date

NON_BUSINESS_CATEGORIES = {
    "LOAN_DISBURSAL", "FD_MATURITY", "REVERSAL_REFUND", "CASH_DEPOSIT"
}

def calculate_monthly_turnover_and_flows(
    transactions: List[Dict[str, Any]],
    emi_attempts: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Computes business turnover, gross credit, non-business credits, debits,
    net flow, EMI burden (successful EMIs only), and EMI-to-Turnover ratio.
    """
    months_data = defaultdict(lambda: {
        "gross_credit": 0.0,
        "business_turnover": 0.0,
        "non_business_credit": 0.0,
        "internal_transfer_credit_excluded": 0.0,
        "total_debit": 0.0,
        "internal_debit_excluded": 0.0,
        "emi_burden": 0.0,
        "emi_bounce_count": 0,
        "gross_credit_count": 0,
        "business_turnover_count": 0,
        "non_business_credit_count": 0
    })

    # 1. Aggregate transactions per month
    for txn in transactions:
        month_str = txn["txn_date"].strftime("%Y-%m")
        credit = float(txn.get("credit", 0.0))
        debit = float(txn.get("debit", 0.0))
        cat = txn.get("category", "UNCATEGORIZED")
        is_internal = txn.get("is_internal_transfer", False)

        if credit > 0:
            months_data[month_str]["gross_credit"] += credit
            months_data[month_str]["gross_credit_count"] += 1

            if is_internal:
                months_data[month_str]["internal_transfer_credit_excluded"] += credit
            elif cat in NON_BUSINESS_CATEGORIES:
                months_data[month_str]["non_business_credit"] += credit
                months_data[month_str]["non_business_credit_count"] += 1
            else:
                months_data[month_str]["business_turnover"] += credit
                months_data[month_str]["business_turnover_count"] += 1

        if debit > 0:
            if is_internal:
                months_data[month_str]["internal_debit_excluded"] += debit
            else:
                months_data[month_str]["total_debit"] += debit

    # 2. Add EMI Burden from SUCCESSFUL attempts only, and count bounces
    for att in emi_attempts:
        m_str = att["attempt_date"].strftime("%Y-%m")
        amt = float(att["amount"])
        if att["status"] == "SUCCESS":
            months_data[m_str]["emi_burden"] += amt
        elif att["status"] == "RETURNED":
            months_data[m_str]["emi_bounce_count"] += 1

    # 3. Format final monthly summaries
    results = []
    for month_str in sorted(months_data.keys()):
        d = months_data[month_str]
        b_turnover = round(d["business_turnover"], 2)
        tot_debit = round(d["total_debit"], 2)
        net_flow = round(b_turnover - tot_debit, 2)
        emi_burden = round(d["emi_burden"], 2)

        ratio = (emi_burden / b_turnover * 100.0) if b_turnover > 0 else 0.0

        results.append({
            "month": month_str,
            "gross_credit": round(d["gross_credit"], 2),
            "business_turnover": b_turnover,
            "non_business_credit": round(d["non_business_credit"], 2),
            "internal_transfer_credit_excluded": round(d["internal_transfer_credit_excluded"], 2),
            "total_debit": tot_debit,
            "net_flow": net_flow,
            "emi_burden": emi_burden,
            "emi_bounce_count": d["emi_bounce_count"],
            "emi_to_turnover_ratio": round(ratio, 2),
            "counts": {
                "gross_credit_count": d["gross_credit_count"],
                "business_turnover_count": d["business_turnover_count"],
                "non_business_credit_count": d["non_business_credit_count"]
            }
        })

    return results

