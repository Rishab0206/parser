import re
from typing import Dict, Any

def classify_transaction(
    narration: str,
    debit: float,
    credit: float,
    channel: str
) -> str:
    """
    Categorizes the transaction based on narration, debit/credit flow, and channel.
    """
    text = (narration or "").upper()

    # Opening balance check
    if any(k in text for k in ["OPENING BALANCE", "BROUGHT FORWARD", "B/F", "OPENING BAL", "BAL B/F"]):
        return "OPENING_BALANCE"

    # 1. Non-business credits: Loan disbursals, FD maturity, reversals
    if credit > 0:
        if any(k in text for k in ["DISBURS", "DISB", "LOAN CR", "FINANCE DISB", "CAPITAL CR"]):
            return "LOAN_DISBURSAL"
        if any(k in text for k in ["FD CLOS", "TERM DEP", "FIXED DEP", "MATURITY", "INT.PD", "INTEREST CR"]):
            return "FD_MATURITY"
        if any(k in text for k in ["REFUND", "REVERSAL", "REV:", "RTN CR", "FAILED TXN REV"]):
            return "REVERSAL_REFUND"
        if any(k in text for k in ["SELF", "OWN AC", "TRANSFER TO SELF", "INTERNAL TRF"]):
            return "INTERNAL_TRANSFER"
        if channel == "CASH" or "BY CASH" in text or "CASH DEP" in text:
            return "CASH_DEPOSIT"
        return "BUSINESS_RECEIPT"

    # 2. Debits
    if debit > 0:
        if any(k in text for k in ["GST", "CGST", "SGST", "IGST", "TAX"]):
            return "TAX"
        if any(k in text for k in ["CHG", "CHARGE", "ANNUAL FEE", "SMS ALERT", "SERVICE TAX"]):
            return "BANK_CHARGES"
        if channel == "CASH" or channel == "ATM" or "TO CASH" in text or "CASH WDL" in text:
            return "CASH_WITHDRAWAL"
        if any(k in text for k in ["NACH", "ACH", "ECS", "EMI", "LOAN DEDUCT", "BAJAJ", "CHOLAMANDALAM"]):
            return "EMI_DEBIT"
        if any(k in text for k in ["SELF", "OWN AC", "TRANSFER TO SELF", "INTERNAL TRF"]):
            return "INTERNAL_TRANSFER"
        return "GENERAL_EXPENSE"

    return "UNCATEGORIZED"

