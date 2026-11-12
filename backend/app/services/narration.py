import re
from typing import Dict, Any, Optional

def extract_channel_and_counterparty(narration: str) -> Dict[str, Any]:
    """
    Extracts payment channel, counterparty, and reference/UTR from raw narration.
    """
    text = (narration or "").strip()
    upper = text.upper()

    channel = "OTHER"
    counterparty = None
    ref_no = None

    if upper.startswith("UPI") or "/UPI/" in upper or " UPI " in upper or "UPI-" in upper:
        channel = "UPI"
        # Match UPI patterns e.g. UPI/DR/123456789012/PAYEE/BANK/REF or UPI-123456789-PAYEE
        parts = text.split("/")
        if len(parts) >= 4:
            counterparty = parts[3].strip()
            ref_no = parts[2].strip()
        else:
            upi_ref = re.search(r'\b\d{12}\b', text)
            if upi_ref:
                ref_no = upi_ref.group(0)

    elif "NEFT" in upper:
        channel = "NEFT"
        neft_match = re.search(r'NEFT[-/\s]([A-Z0-9]+)[-/\s]([A-Za-z0-9\s]+)', text, re.IGNORECASE)
        if neft_match:
            ref_no = neft_match.group(1)
            counterparty = neft_match.group(2).strip()

    elif "RTGS" in upper:
        channel = "RTGS"
        rtgs_match = re.search(r'RTGS[-/\s]([A-Z0-9]+)[-/\s]([A-Za-z0-9\s]+)', text, re.IGNORECASE)
        if rtgs_match:
            ref_no = rtgs_match.group(1)
            counterparty = rtgs_match.group(2).strip()

    elif "IMPS" in upper:
        channel = "IMPS"
        imps_ref = re.search(r'\b\d{12}\b', text)
        if imps_ref:
            ref_no = imps_ref.group(0)
        # Extract counterparty after P2A or ref
        imps_cp = re.search(r'IMPS[/-][0-9]+[/-]([A-Za-z0-9\s]+)', text)
        if imps_cp:
            counterparty = imps_cp.group(1).strip()

    elif any(k in upper for k in ["NACH", "NACH-DR", "E-NACH"]):
        channel = "NACH"
        nach_ref = re.search(r'\b([A-Z0-9]{10,20})\b', text)
        if nach_ref:
            ref_no = nach_ref.group(1)
        # Counterparty is typically the mandate sponsor/lender
        nach_parts = text.split("-")
        if len(nach_parts) > 1:
            counterparty = nach_parts[1].strip()

    elif "ACH" in upper or "ACH D-" in upper:
        channel = "ACH"
    elif "ECS" in upper or "ECS-DR" in upper:
        channel = "ECS"
    elif "CHEQUE" in upper or "CHQ" in upper or "CLEARING" in upper:
        channel = "CHEQUE"
        chq_match = re.search(r'\b(\d{6})\b', text)
        if chq_match:
            ref_no = chq_match.group(1)
    elif "ATM" in upper or "NFS" in upper or "CASH WDL" in upper:
        channel = "ATM"
    elif "POS" in upper or "EDC" in upper:
        channel = "POS"
    elif "CASH DEP" in upper or "BY CASH" in upper or "TO CASH" in upper or upper.startswith("CASH"):
        channel = "CASH"
    elif "DEBIT CARD" in upper or "CREDIT CARD" in upper or "VISA" in upper or "MASTERCARD" in upper:
        channel = "CARD"

    # Clean counterparty if present, else ensure it's explicitly None
    if counterparty:
        counterparty = re.sub(r'[^A-Za-z0-9\s.&]', '', counterparty).strip()[:100]
        if not counterparty:
            counterparty = None
    else:
        counterparty = None

    return {
        "channel": channel,
        "counterparty": counterparty,
        "ref_no": ref_no
    }

