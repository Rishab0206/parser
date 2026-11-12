import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import date, timedelta

RETURN_KEYWORDS = [
    "RETURN", "RTRN", "RET", "ECS RETURN", "NACH RETURN", "UNPAID", "INSUFFICIENT", "BOUNCE"
]

CHARGE_KEYWORDS = [
    "RTN CHG", "RETURN CHG", "RETURN CHARGES", "ECS RTN CHG", "NACH RTN CHG", "CHQ RET CHG", "BOUNCE CHG"
]

def reconcile_returns_and_charges(
    transactions: List[Dict[str, Any]],
    emi_attempts: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Matches return credits and separate bounce charges against EMI attempts.
    Returns: (return_records, review_items)
    """
    return_records = []
    review_items = []

    # 1. Separate return credits and charges
    return_candidates = []
    charge_candidates = []

    for txn in transactions:
        narr = txn.get("narration_raw", "").upper()
        credit = float(txn.get("credit", 0.0))
        debit = float(txn.get("debit", 0.0))

        # Check for bounce/return charges (debit)
        if debit > 0 and any(k in narr for k in CHARGE_KEYWORDS):
            charge_candidates.append(txn)

        # Check for return reversals (credit equal to EMI or return keyword)
        if credit > 0 and any(k in narr for k in RETURN_KEYWORDS):
            return_candidates.append(txn)

    # Track matched return txn IDs to prevent double counting
    matched_return_txn_ids = set()
    matched_attempts = set()

    # 2. Match return credit with EMI attempt within 0-7 days (up to 10 days if ref matches)
    for ret_txn in return_candidates:
        ret_date = ret_txn["txn_date"]
        ret_amt = float(ret_txn["credit"])
        ret_narr = ret_txn["narration_raw"].upper()
        ret_ref = ret_txn.get("ref_no")

        best_attempt = None
        ambiguous_attempts = []

        for att in emi_attempts:
            att_id = att.get("transaction_id") or id(att)
            if att_id in matched_attempts:
                continue

            att_date = att["attempt_date"]
            gap = (ret_date - att_date).days
            if gap < 0:
                continue

            att_amt = float(att["amount"])
            amt_diff = abs(ret_amt - att_amt)

            # Amount match tolerance ₹1.00
            if amt_diff <= 1.0:
                # Normal window 0-7 days, or up to 10 days if ref/mandate match
                if gap <= 7 or (gap <= 10 and ret_ref and ret_ref in att["transaction"].get("narration_raw", "")):
                    ambiguous_attempts.append(att)

        if len(ambiguous_attempts) == 1:
            best_attempt = ambiguous_attempts[0]
        elif len(ambiguous_attempts) > 1:
            # Check if one has exact ref match
            ref_matches = [a for a in ambiguous_attempts if ret_ref and ret_ref in a["transaction"].get("narration_raw", "")]
            if len(ref_matches) == 1:
                best_attempt = ref_matches[0]
            else:
                # Ambiguous match: send BOTH to Review Queue
                review_items.append({
                    "issue_type": "AMBIGUOUS_RETURN_MATCH",
                    "confidence": 45.0,
                    "suggested_value": {
                        "return_txn": ret_txn["id"] if "id" in ret_txn else None,
                        "candidate_attempts": [a["transaction_id"] for a in ambiguous_attempts],
                        "amount": ret_amt,
                        "date": str(ret_date)
                    },
                    "source_page_no": ret_txn["source_page_no"],
                    "narration_raw": ret_txn["narration_raw"]
                })
                continue

        if best_attempt:
            att_id = best_attempt.get("transaction_id") or id(best_attempt)
            matched_attempts.add(att_id)
            matched_return_txn_ids.add(ret_txn.get("id") or id(ret_txn))

            # Mark attempt as RETURNED
            best_attempt["status"] = "RETURNED"

            # 3. Find matching bounce charge debit within 0-3 days of return date
            matched_charge = None
            for chg in charge_candidates:
                chg_date = chg["txn_date"]
                chg_gap = abs((chg_date - ret_date).days)
                if chg_gap <= 3:
                    matched_charge = chg
                    break

            charge_amt = float(matched_charge["debit"]) if matched_charge else 0.0
            charge_id = matched_charge.get("id") if matched_charge else None

            # 4. Check for recovery (re-presentation within 30 days with same amount)
            recovery_status = "NOT_RECOVERED"
            recovery_txn = None
            for t in transactions:
                if float(t.get("debit", 0.0)) > 0:
                    t_gap = (t["txn_date"] - ret_date).days
                    if 1 <= t_gap <= 30 and abs(float(t["debit"]) - ret_amt) <= 1.0:
                        # Re-presentation found
                        recovery_status = "RECOVERED"
                        recovery_txn = t
                        break

            return_rec = {
                "emi_attempt_id": best_attempt.get("id"),
                "original_txn_id": best_attempt.get("transaction_id"),
                "return_txn_id": ret_txn.get("id"),
                "return_date": ret_date,
                "return_amount": ret_amt,
                "return_charge_amount": charge_amt,
                "charge_txn_id": charge_id,
                "reason": "INSUFFICIENT_FUNDS" if "INSUFFICIENT" in ret_narr else "OTHER",
                "recovery_status": recovery_status,
                "recovery_txn_id": recovery_txn.get("id") if recovery_txn else None,
                "source_page_no": ret_txn["source_page_no"],
                "lender_name": best_attempt.get("transaction", {}).get("counterparty") or "Lender",
                "original_emi_date": best_attempt["attempt_date"],
                "original_txn_narration": best_attempt["transaction"].get("narration_raw"),
                "return_txn_narration": ret_txn["narration_raw"]
            }
            return_records.append(return_rec)

    return return_records, review_items

