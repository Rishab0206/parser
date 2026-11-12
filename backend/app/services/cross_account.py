import uuid
from typing import List, Dict, Any, Tuple
from datetime import date

OWN_TRANSFER_KEYWORDS = [
    "SELF", "OWN", "FUND TRANSFER", "INTERNAL", "TRF TO", "TRF FROM", "OWN A/C", "SELF TRANSFER"
]

def reconcile_cross_account_transfers(
    statements_transactions: Dict[str, List[Dict[str, Any]]],
    customer_name: str = ""
) -> Tuple[List[Tuple[Dict[str, Any], Dict[str, Any]]], List[Dict[str, Any]]]:
    """
    Reconciles internal fund transfers between multiple accounts of the same customer/application.
    Returns: (confirmed_matches, review_items)
    """
    statement_ids = list(statements_transactions.keys())
    if len(statement_ids) < 2:
        return [], []

    confirmed_matches = []
    review_items = []
    matched_ids = set()

    # Compare account pairs
    for i in range(len(statement_ids)):
        stmt_a_id = statement_ids[i]
        txns_a = statements_transactions[stmt_a_id]

        for j in range(i + 1, len(statement_ids)):
            stmt_b_id = statement_ids[j]
            txns_b = statements_transactions[stmt_b_id]

            # Compare debits in A with credits in B
            for t_a in txns_a:
                debit_a = float(t_a.get("debit", 0.0))
                if debit_a <= 0:
                    continue
                t_a_id = t_a.get("id") or id(t_a)
                if t_a_id in matched_ids:
                    continue

                for t_b in txns_b:
                    credit_b = float(t_b.get("credit", 0.0))
                    if credit_b <= 0:
                        continue
                    t_b_id = t_b.get("id") or id(t_b)
                    if t_b_id in matched_ids:
                        continue

                    # Check amount equality within ₹1.00
                    if abs(debit_a - credit_b) > 1.0:
                        continue

                    gap = abs((t_a["txn_date"] - t_b["txn_date"]).days)

                    # Narration check for own-transfer keywords or customer name
                    narr_a = t_a.get("narration_raw", "").upper()
                    narr_b = t_b.get("narration_raw", "").upper()
                    has_own_kw = any(k in narr_a or k in narr_b for k in OWN_TRANSFER_KEYWORDS)
                    cust_upper = customer_name.upper().strip() if customer_name else ""
                    has_name = len(cust_upper) > 3 and (cust_upper in narr_a or cust_upper in narr_b)

                    # 1. CONFIRMED INTERNAL: gap 0-1 day + own name / keywords
                    if gap <= 1 and (has_own_kw or has_name):
                        match_uuid = str(uuid.uuid4())
                        t_a["is_internal_transfer"] = True
                        t_a["internal_match_id"] = match_uuid
                        t_b["is_internal_transfer"] = True
                        t_b["internal_match_id"] = match_uuid
                        matched_ids.add(t_a_id)
                        matched_ids.add(t_b_id)
                        confirmed_matches.append((t_a, t_b))
                        break

                    # 2. UNCERTAIN (REVIEW QUEUE): gap 2-3 days or gap 0-1 day without clear keyword
                    elif gap <= 3:
                        review_items.append({
                            "issue_type": "CROSS_ACCOUNT_REVIEW",
                            "confidence": 50.0,
                            "suggested_value": {
                                "stmt_debit_id": stmt_a_id,
                                "stmt_credit_id": stmt_b_id,
                                "debit_txn_id": t_a.get("id"),
                                "credit_txn_id": t_b.get("id"),
                                "amount": debit_a,
                                "date_a": str(t_a["txn_date"]),
                                "date_b": str(t_b["txn_date"]),
                                "gap_days": gap
                            },
                            "source_page_no": t_a.get("source_page_no", 1),
                            "narration_raw": f"Possible transfer: {t_a.get('narration_raw')} <-> {t_b.get('narration_raw')}",
                            "amount": debit_a,
                            "date": t_a["txn_date"]
                        })

    return confirmed_matches, review_items

