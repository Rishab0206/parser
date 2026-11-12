import re
from typing import Dict, Any, Optional, Tuple
from app.parsers.generic_parser import BankParserEngine

parser_engine = BankParserEngine()

def detect_bank_and_account(
    full_text: str
) -> Dict[str, Any]:
    """
    Extracts bank metadata, account number, IFSC, and account type (SAVINGS/CURRENT/OD/CC).
    """
    detected_cfg, confidence = parser_engine.detect_bank_from_text(full_text)
    bank_name = detected_cfg.get("bank_name", "Unknown Bank") if detected_cfg else "Unknown Bank"
    bank_code = detected_cfg.get("bank_code", "UNKNOWN") if detected_cfg else "UNKNOWN"

    # Extract IFSC
    ifsc = None
    ifsc_match = re.search(r'\b([A-Z]{4}0[A-Z0-9]{6})\b', full_text)
    if ifsc_match:
        ifsc = ifsc_match.group(1)

    # Extract Account Number
    # Match patterns like "Account No: 1234567890", "A/c No : 501002345678", etc.
    account_no = None
    acc_patterns = [
        r'(?:Account\s*(?:No|Number)|A/c\s*(?:No|Number)?|Acc\s*No)[\s.:#]*([0-9]{9,18})\b',
        r'\b([0-9]{11,18})\b'
    ]
    for pat in acc_patterns:
        match = re.search(pat, full_text, re.IGNORECASE)
        if match:
            account_no = match.group(1)
            break

    # Extract Account Type
    account_type = "SAVINGS"
    upper_text = full_text.upper()
    if "CURRENT ACCOUNT" in upper_text or "CA A/C" in upper_text or "CURRENT A/C" in upper_text:
        account_type = "CURRENT"
    elif "OVERDRAFT" in upper_text or "OD ACCOUNT" in upper_text or "OD A/C" in upper_text:
        account_type = "OD"
    elif "CASH CREDIT" in upper_text or "CC A/C" in upper_text:
        account_type = "CC"
    elif "SAVINGS" in upper_text or "SB A/C" in upper_text:
        account_type = "SAVINGS"

    # Extract Branch
    branch = None
    branch_match = re.search(r'Branch[\s.:]+([A-Za-z0-9\s,\-]+?)(?:\n|IFSC|Pin|\bDate\b)', full_text, re.IGNORECASE)
    if branch_match:
        branch = branch_match.group(1).strip()[:80]

    # Extract Statement Period
    period_str = None
    period_match = re.search(r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s*[-–toTO\s]+\s*\d{1,2}\s+[A-Za-z]{3}\s+\d{4})', full_text)
    if period_match:
        period_str = period_match.group(1).strip()
    else:
        period_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\s*[-–toTO\s]+\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', full_text)
        if period_match:
            period_str = period_match.group(1).strip()

    # Extract Customer / Account Holder Name
    customer_name = None
    labeled_patterns = [
        r'(?:Customer\s*Name|Name\s*of\s*(?:the\s*)?Account\s*Holder|Account\s*Holder\s*Name|Account\s*Name|A/c\s*Name)[\s.:\-]+([A-Za-z\s\.\,\'\-]{3,60})',
        r'(?:Name\s*:)[\s]*([A-Za-z\s\.\,\'\-]{3,60})',
        r'(?:Mr\.|Ms\.|Mrs\.|M/s\.)\s+([A-Za-z\s\.\,\'\-]{3,60})'
    ]
    for pat in labeled_patterns:
        m = re.search(pat, full_text, re.IGNORECASE)
        if m:
            cand = m.group(1).strip().split('\n')[0].strip()
            if len(cand) >= 3 and not any(k in cand.upper() for k in ['STATEMENT', 'BANK', 'BRANCH', 'ACCOUNT', 'PAGE', 'SUMMARY', 'NOMINEE']):
                customer_name = cand
                break

    # Positional pattern (Kotak & standard statement top layouts)
    if not customer_name:
        lines = [l.strip() for l in full_text.split('\n') if l.strip()]
        for i, line in enumerate(lines[:15]):
            if re.search(r'\d{1,2}\s+[A-Za-z]{3}\s+\d{4}\s*[-–]\s*\d{1,2}\s+[A-Za-z]{3}\s+\d{4}', line):
                if i + 1 < len(lines):
                    cand = lines[i + 1].strip()
                    words = cand.split()
                    if 2 <= len(words) <= 5 and all(w.replace('.', '').isalpha() for w in words):
                        if not any(k in cand.upper() for k in ['STATEMENT', 'BANK', 'BRANCH', 'ACCOUNT', 'CRN', 'PAGE', 'SUMMARY', 'NOMINEE']):
                            customer_name = cand
                            break

    return {
        "bank_name": bank_name,
        "bank_code": bank_code,
        "bank_detect_confidence": confidence,
        "account_no": account_no,
        "account_type": account_type,
        "ifsc": ifsc,
        "branch": branch,
        "customer_name": customer_name,
        "period_str": period_str,
        "config": detected_cfg
    }

