import pytest
from datetime import date
from app.parsers.generic_parser import BankParserEngine

engine = BankParserEngine()

def test_kotak_parser():
    # Kotak header: Date | Description | Chq/Ref | Withdrawal Dr | Deposit Cr | Balance
    cfg, conf = engine.detect_bank_from_text("KOTAK MAHINDRA BANK IFSC: KKBK0001234")
    assert cfg is not None
    assert cfg["bank_code"] == "KOTAK"
    assert conf >= 80.0

    raw_table = [
        ["Date", "Description", "Chq/Ref", "Withdrawal Dr", "Deposit Cr", "Balance"],
        ["01/04/2026", "OPENING BALANCE", "", "", "", "1,50,000.00"],
        ["05/04/2026", "NACH-DR-BAJAJ FINANCE-12345", "REF9876", "12,500.00", "", "1,37,500.00"],
        ["10/04/2026", "NEFT-CLIENT PAYMENT-ABC CORP", "UTR0011", "", "50,000.00", "1,87,500.00"],
        ["15/04/2026", "UPI/DR/1234567890/VENDOR/HDFC/PAY", "", "5,000.00", "", "1,82,500.00"]
    ]

    txns, revs = engine.parse_raw_rows(raw_table, cfg, source_page_no=1)
    # 4 rows including Opening Balance
    assert len(txns) == 4
    assert txns[0]["category"] == "OPENING_BALANCE"
    assert txns[0]["counterparty"] is None
    assert txns[0]["balance"] == 150000.0
    assert txns[1]["debit"] == 12500.0
    assert txns[2]["credit"] == 50000.0
    assert txns[3]["balance"] == 182500.0

def test_hdfc_parser():
    cfg, conf = engine.detect_bank_from_text("HDFC BANK LTD IFSC: HDFC0000456")
    assert cfg is not None
    assert cfg["bank_code"] == "HDFC"

    raw_table = [
        ["Date", "Narration", "Chq/Ref", "Value Dt", "Withdrawal", "Deposit", "Closing Balance"],
        ["01/05/2026", "BROUGHT FORWARD", "", "01/05/2026", "", "", "2,00,000.00"],
        ["04/05/2026", "ACH D- TATA CAPITAL-8989", "CHQ001", "04/05/2026", "15,000.00", "", "1,85,000.00"],
        ["12/05/2026", "CUSTOMER SALES RECEIPT", "REF002", "12/05/2026", "", "40,000.00", "2,25,000.00"]
    ]

    txns, revs = engine.parse_raw_rows(raw_table, cfg, source_page_no=1)
    assert len(txns) == 3
    assert txns[0]["category"] == "OPENING_BALANCE"
    assert txns[0]["counterparty"] is None
    assert txns[1]["debit"] == 15000.0
    assert txns[2]["credit"] == 40000.0
    assert txns[2]["balance"] == 225000.0

def test_icici_parser():
    cfg, conf = engine.detect_bank_from_text("ICICI BANK STATEMENT IFSC: ICIC0000999")
    assert cfg is not None
    assert cfg["bank_code"] == "ICICI"

    raw_table = [
        ["Txn Date", "Value Date", "Description", "Ref", "Debit", "Credit", "Balance"],
        ["02/06/2026", "02/06/2026", "OPENING BALANCE", "", "", "", "80,000.00"],
        ["07/06/2026", "07/06/2026", "ACH/ CHOLAMANDALAM/ 3456", "REF3456", "8,200.00", "", "71,800.00"],
        ["18/06/2026", "18/06/2026", "INFT/NEFT/INVOICE 101", "UTR9988", "", "65,000.00", "1,36,800.00"]
    ]

    txns, revs = engine.parse_raw_rows(raw_table, cfg, source_page_no=1)
    assert len(txns) == 3
    assert txns[0]["category"] == "OPENING_BALANCE"
    assert txns[0]["counterparty"] is None
    assert txns[1]["debit"] == 8200.0
    assert txns[2]["balance"] == 136800.0

def test_sbi_parser():
    cfg, conf = engine.detect_bank_from_text("STATE BANK OF INDIA IFSC: SBIN0001111")
    assert cfg is not None
    assert cfg["bank_code"] == "SBI"

    raw_table = [
        ["Transaction Date", "Value Date", "Description", "Ref", "Debit", "Credit", "Balance"],
        ["01 Jul 2026", "01 Jul 2026", "OPENING BALANCE", "", "", "", "50,000.00"],
        ["05 Jul 2026", "05 Jul 2026", "BULK POSTING NACH/DR/BAJAJ", "NACH77", "10,000.00", "", "40,000.00"],
        ["20 Jul 2026", "20 Jul 2026", "BY CLEARING CHEQUE DEPOSIT", "CHQ100", "", "75,000.00", "1,15,000.00"]
    ]

    txns, revs = engine.parse_raw_rows(raw_table, cfg, source_page_no=1)
    assert len(txns) == 3
    assert txns[0]["category"] == "OPENING_BALANCE"
    assert txns[0]["counterparty"] is None
    assert txns[1]["debit"] == 10000.0
    assert txns[2]["credit"] == 75000.0

def test_axis_parser():
    cfg, conf = engine.detect_bank_from_text("AXIS BANK IFSC: UTIB0000222")
    assert cfg is not None
    assert cfg["bank_code"] == "AXIS"

    raw_table = [
        ["Tran Date", "Chq No", "Particulars", "Debit", "Credit", "Balance", "Init Br"],
        ["01-08-2026", "", "OPENING BALANCE", "", "", "90,000.00", "MUMBAI"],
        ["05-08-2026", "CHQ01", "ACH/DR/HDB FINANCIAL", "6,500.00", "", "83,500.00", "MUMBAI"],
        ["14-08-2026", "", "NEFT CR-TRADE RECEIPT", "", "30,000.00", "1,13,500.00", "MUMBAI"]
    ]

    txns, revs = engine.parse_raw_rows(raw_table, cfg, source_page_no=1)
    assert len(txns) == 3
    assert txns[0]["category"] == "OPENING_BALANCE"
    assert txns[0]["counterparty"] is None
    assert txns[1]["debit"] == 6500.0
    assert txns[2]["balance"] == 113500.0

def test_yes_bank_parser():
    cfg, conf = engine.detect_bank_from_text("YES BANK STATEMENT IFSC: YESB0000333")
    assert cfg is not None
    assert cfg["bank_code"] == "YES"

    raw_table = [
        ["Date", "Narration", "Chq/Ref", "Withdrawal", "Deposit", "Balance"],
        ["01/09/2026", "BROUGHT FORWARD", "", "", "", "1,20,000.00"],
        ["06/09/2026", "NACH DR SHRIRAM FINANCE", "REF445", "11,000.00", "", "1,09,000.00"],
        ["15/09/2026", "RTGS CR-SERVICES PAYMENT", "RTGS88", "", "90,000.00", "1,99,000.00"]
    ]

    txns, revs = engine.parse_raw_rows(raw_table, cfg, source_page_no=1)
    assert len(txns) == 3
    assert txns[0]["category"] == "OPENING_BALANCE"
    assert txns[0]["counterparty"] is None
    assert txns[1]["debit"] == 11000.0
    assert txns[2]["credit"] == 90000.0

def test_federal_bank_parser():
    cfg, conf = engine.detect_bank_from_text("FEDERAL BANK IFSC: FDRL0000444")
    assert cfg is not None
    assert cfg["bank_code"] == "FEDERAL"

    raw_table = [
        ["Date", "Description", "Cheque No", "Debit", "Credit", "Balance"],
        ["01/10/2026", "OPENING BALANCE", "", "", "", "60,000.00"],
        ["05/10/2026", "FEDNET/LOAN EMI/KOTAK PRIME", "REF22", "7,800.00", "", "52,200.00"],
        ["22/10/2026", "BY CASH DEPOSIT", "", "", "25,000.00", "77,200.00"]
    ]

    txns, revs = engine.parse_raw_rows(raw_table, cfg, source_page_no=1)
    assert len(txns) == 3
    assert txns[0]["category"] == "OPENING_BALANCE"
    assert txns[0]["counterparty"] is None
    assert txns[1]["debit"] == 7800.0
    assert txns[2]["balance"] == 77200.0
