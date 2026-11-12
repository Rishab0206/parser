import pytest
from datetime import date
from app.parsers.generic_parser import BankParserEngine
from app.services.narration import extract_channel_and_counterparty
from app.services.classify import classify_transaction

engine = BankParserEngine()

def test_null_counterparty_and_opening_balance():
    # Table containing: Opening Balance, SMS charge, GST, and standard UPI
    raw_table = [
        ["Date", "Description", "Chq/Ref", "Withdrawal Dr", "Deposit Cr", "Balance"],
        ["01/06/2026", "OPENING BALANCE", "", "", "", "10,000.00"],
        ["02/06/2026", "REM CHRG:SMS ALERT FEE FOR THE QTR", "", "17.70", "", "9,982.30"],
        ["03/06/2026", "GST TAX PAYMENT", "", "3.18", "", "9,979.12"],
        ["04/06/2026", "UPI/GUJARAT METRO/651912345678", "", "30.00", "", "9,949.12"]
    ]

    txns, revs = engine.parse_raw_rows(raw_table, None, source_page_no=1)
    assert len(txns) == 4

    # 1. Opening balance row
    assert txns[0]["category"] == "OPENING_BALANCE"
    assert txns[0]["counterparty"] is None
    assert txns[0]["balance"] == 10000.0

    # 2. SMS alert charges
    meta_sms = extract_channel_and_counterparty(txns[1]["narration_raw"])
    cat_sms = classify_transaction(txns[1]["narration_raw"], txns[1]["debit"], txns[1]["credit"], meta_sms["channel"])
    assert cat_sms == "BANK_CHARGES"
    assert meta_sms["counterparty"] is None

    # 3. GST tax
    meta_gst = extract_channel_and_counterparty(txns[2]["narration_raw"])
    cat_gst = classify_transaction(txns[2]["narration_raw"], txns[2]["debit"], txns[2]["credit"], meta_gst["channel"])
    assert cat_gst == "TAX"
    assert meta_gst["counterparty"] is None

def test_row_error_does_not_abort_entire_file():
    # If one row has completely malformed data, other rows must still be parsed successfully
    raw_table = [
        ["Date", "Description", "Chq/Ref", "Withdrawal Dr", "Deposit Cr", "Balance"],
        ["01/06/2026", "OPENING BALANCE", "", "", "", "5,000.00"],
        ["INVALID_DATE", "CORRUPTED ROW", "", "BAD_AMT", "", "BAD_BAL"],
        ["05/06/2026", "NEFT-CLIENT PAYMENT-ABC", "UTR123", "", "15,000.00", "20,000.00"]
    ]

    txns, revs = engine.parse_raw_rows(raw_table, None, source_page_no=1)
    # The valid transactions (Opening Balance + NEFT) are preserved!
    assert len(txns) == 2
    assert txns[0]["balance"] == 5000.0
    assert txns[1]["credit"] == 15000.0

