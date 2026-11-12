import re
from typing import List, Dict, Any, Tuple, Optional
from datetime import date, timedelta
from decimal import Decimal

# Known non-EMI exclusion list
NOT_EMI_EXCLUSIONS = [
    "SIP", "MUTUAL FUND", "MF", "NIPPON", "HDFC MF", "SBI MF", "ICICI PRU MF", "UTI", "MIRAE",
    "LIC", "INSURANCE", "PREMIUM", "MAX LIFE", "STAR HEALTH", "HDFC LIFE", "ICICI PRUDENTIAL",
    "TATA AIA", "BAJAJ ALLIANZ LIFE", "CARE HEALTH",
    "RENT", "OFFICE RENT", "HOUSE RENT",
    "SALARY", "PAYROLL", "STIPEND",
    "NETFLIX", "AMAZON PRIME", "HOTSTAR", "SPOTIFY", "SUBSCRIPTION",
    "SCHOOL", "COLLEGE", "TUITION", "FEE",
    "ELECTRICITY", "BESCOM", "MSEDCL", "WATER BILL", "GAS BILL", "BROADBAND", "AIRTEL", "JIO"
]

# Common Indian Lenders for normalization
KNOWN_LENDERS = {
    "BAJAJ": "Bajaj Finance",
    "BAJAJFIN": "Bajaj Finance",
    "BAJAJ FINSERV": "Bajaj Finance",
    "BAJAJ FINANCE": "Bajaj Finance",
    "HDFC BANK LOAN": "HDFC Bank",
    "HDB FINANCIAL": "HDB Financial Services",
    "HDBFS": "HDB Financial Services",
    "TATA CAPITAL": "Tata Capital",
    "CHOLAMANDALAM": "Cholamandalam Investment",
    "CHOLA": "Cholamandalam Investment",
    "MAHINDRA": "Mahindra Finance",
    "MMFSL": "Mahindra Finance",
    "SHRIRAM": "Shriram Finance",
    "IDFC FIRST": "IDFC FIRST Bank",
    "KOTAK MAHINDRA PRIME": "Kotak Mahindra Prime",
    "ADITYA BIRLA": "Aditya Birla Capital",
    "ABFL": "Aditya Birla Finance",
    "POONAWALLA": "Poonawalla Fincorp",
    "L&T FINANCE": "L&T Finance",
    "FULLERTON": "SMFG India Credit (Fullerton)",
    "PIRAMAL": "Piramal Capital",
    "HERO FINCORP": "Hero FinCorp",
    "MUTHOOT": "Muthoot Finance",
    "MANAPPURAM": "Manappuram Finance",
    "IIFL": "IIFL Finance",
    "AXIS BANK LOAN": "Axis Bank",
    "ICICI BANK LOAN": "ICICI Bank",
    "SBI LOAN": "State Bank of India"
}

def normalize_lender_name(narration: str) -> Optional[str]:
    upper = (narration or "").upper()
    for key, canonical in KNOWN_LENDERS.items():
        if key in upper:
            return canonical

    # Extract counterparty if NACH-DR pattern: NACH-DR-<LENDER>-<REF>
    nach_match = re.search(r'NACH(?:-DR)?[-/\s]+([A-Za-z0-9\s]+?)[-/\s]+', upper)
    if nach_match:
        cand = nach_match.group(1).strip()
        if len(cand) >= 3 and not any(ex in cand for ex in ["DEBIT", "RETURN", "BOUNCE"]):
            return cand.title()

    return None

def is_excluded_recurring(narration: str) -> bool:
    upper = (narration or "").upper()
    for ex in NOT_EMI_EXCLUSIONS:
        if re.search(r'\b' + re.escape(ex) + r'\b', upper):
            return True
    return False

def determine_frequency(dates: List[date]) -> str:
    if len(dates) < 2:
        return "MONTHLY"
    sorted_dates = sorted(dates)
    gaps = [(sorted_dates[i] - sorted_dates[i-1]).days for i in range(1, len(sorted_dates))]
    avg_gap = sum(gaps) / len(gaps)

    if 6 <= avg_gap <= 8:
        return "WEEKLY"
    elif 24 <= avg_gap <= 36:
        return "MONTHLY"
    elif 80 <= avg_gap <= 100:
        return "QUARTERLY"
    else:
        return "VARIABLE"

def detect_emi_intelligence(
    transactions: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Detects and classifies EMI records and attempts from transactions.
    Returns: (confirmed_probable_emis, possible_emis_for_review, emi_attempts)
    """
    # 1. Filter debit transactions
    debits = [t for t in transactions if float(t.get("debit", 0.0)) > 0]

    # Candidate tracking: group by (lender_or_counterparty, amount_rounded)
    candidates = {}

    for txn in debits:
        narr = txn.get("narration_raw", "")
        # Check exclusion list (SIP, Rent, etc.)
        if is_excluded_recurring(narr):
            continue

        upper_narr = narr.upper()
        amt = float(txn["debit"])
        if amt < 500.0:  # Minimal threshold for loan EMI
            continue

        has_nach_keyword = any(k in upper_narr for k in ["NACH", "ACH", "ECS", "E-NACH", "MANDATE", "EMI"])
        lender = normalize_lender_name(narr)

        # Extract mandate reference if present
        mandate_ref = None
        mandate_match = re.search(r'\b(UMRN[A-Z0-9]+|[A-Z]{4}\d{10,20})\b', upper_narr)
        if mandate_match:
            mandate_ref = mandate_match.group(1)

        key_lender = lender or txn.get("counterparty") or "UNKNOWN_LENDER"
        # Group by (lender, rounded amount) so multiple loans with same lender stay separate
        amt_bucket = round(amt, -1)  # Bucket within ₹10
        group_key = f"{key_lender}_{amt_bucket}"

        if group_key not in candidates:
            candidates[group_key] = {
                "lender_name": key_lender,
                "mandate_ref": mandate_ref,
                "sample_amount": amt,
                "has_nach_keyword": has_nach_keyword,
                "transactions": []
            }

        candidates[group_key]["transactions"].append(txn)
        if has_nach_keyword:
            candidates[group_key]["has_nach_keyword"] = True
        if mandate_ref and not candidates[group_key]["mandate_ref"]:
            candidates[group_key]["mandate_ref"] = mandate_ref

    confirmed_probable_emis = []
    possible_emis = []
    emi_attempts = []

    for group_key, group in candidates.items():
        txns = group["transactions"]
        txns.sort(key=lambda x: x["txn_date"])
        dates = [t["txn_date"] for t in txns]
        freq = determine_frequency(dates)
        avg_amt = sum(float(t["debit"]) for t in txns) / len(txns)

        # Classification rules:
        # CONFIRMED: has NACH/EMI keyword + known lender/mandate
        # PROBABLE: repeats >= 2 times with consistent gap (weekly/monthly/quarterly), but no EMI keyword
        # POSSIBLE: repeats but irregular gap or variable amount

        is_confirmed = group["has_nach_keyword"] and (group["lender_name"] != "UNKNOWN_LENDER" or group["mandate_ref"])
        is_probable = (not group["has_nach_keyword"]) and len(txns) >= 2 and freq in ["MONTHLY", "WEEKLY", "QUARTERLY"]

        if is_confirmed:
            confidence_level = "CONFIRMED"
        elif is_probable:
            confidence_level = "PROBABLE"
        elif len(txns) >= 2 or group["has_nach_keyword"]:
            confidence_level = "POSSIBLE"
        else:
            continue

        emi_record = {
            "lender_name": group["lender_name"],
            "lender_confidence": confidence_level,
            "mandate_ref": group["mandate_ref"],
            "amount": round(avg_amt, 2),
            "frequency": freq,
            "first_date": dates[0],
            "last_date": dates[-1],
            "total_attempts": len(txns),
            "total_success": 0,  # Updated after return matching
            "total_returns": 0,
            "status": "ACTIVE"
        }

        # Build attempts
        for t in txns:
            emi_attempts.append({
                "group_key": group_key,
                "transaction_id": t.get("id"),
                "transaction": t,
                "attempt_date": t["txn_date"],
                "amount": float(t["debit"]),
                "status": "SUCCESS"  # Default success until return match
            })

        if confidence_level in ["CONFIRMED", "PROBABLE"]:
            confirmed_probable_emis.append((group_key, emi_record))
        else:
            possible_emis.append((group_key, emi_record))

    return confirmed_probable_emis, possible_emis, emi_attempts

