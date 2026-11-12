import os
import re
import json
import glob
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from decimal import Decimal

CONFIGS_DIR = os.path.join(os.path.dirname(__file__), "bank_configs")

def load_bank_configs() -> List[Dict[str, Any]]:
    configs = []
    config_files = glob.glob(os.path.join(CONFIGS_DIR, "*.json"))
    for file_path in config_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
                configs.append(cfg)
        except Exception:
            continue
    return configs

def parse_indian_amount(amt_str: Any) -> Optional[float]:
    """
    Parses amounts formatted with Indian numbering (e.g. 1,00,000.00),
    parentheses for negative (1,000.00), Dr/Cr suffix, or trailing minus.
    """
    if amt_str is None:
        return None
    val = str(amt_str).strip()
    if not val or val == "-" or val == "—":
        return 0.0

    # Handle (1000.00) negative
    is_negative = False
    if val.startswith("(") and val.endswith(")"):
        is_negative = True
        val = val[1:-1].strip()

    # Handle Dr / Cr in string
    if val.upper().endswith("DR"):
        is_negative = True
        val = val[:-2].strip()
    elif val.upper().endswith("CR"):
        val = val[:-2].strip()

    # Remove Indian commas, spaces, currency symbols
    val = re.sub(r"[₹Rs\.INR\s,]", "", val)
    # Re-insert decimal if cleaned
    # Check if original had decimal
    orig_cleaned = str(amt_str).strip().replace("₹", "").replace("Rs.", "").replace("INR", "").replace(" ", "").replace(",", "")
    match = re.search(r'[-+]?\d*\.?\d+', orig_cleaned)
    if not match:
        return None

    try:
        num = float(match.group(0))
        if is_negative or "-" in str(amt_str):
            num = -abs(num)
        return round(num, 2)
    except ValueError:
        return None

def parse_date_string(date_str: str, bank_formats: List[str] = None) -> Optional[date]:
    if not date_str:
        return None
    cleaned = str(date_str).strip()
    formats = bank_formats or []
    default_formats = [
        "%d/%m/%Y", "%d-%m-%Y", "%d %b %Y", "%d-%b-%Y",
        "%d/%m/%y", "%d-%m-%y", "%Y-%m-%d", "%d.%m.%Y",
        "%d %B %Y", "%b %d, %Y"
    ]
    all_formats = formats + [f for f in default_formats if f not in formats]

    for fmt in all_formats:
        try:
            return datetime.strptime(cleaned, fmt).date()
        except (ValueError, TypeError):
            continue
    return None

class BankParserEngine:
    """
    Universal configurable banking parser engine.
    Driven by JSON configuration schemas with generic keyword fallback.
    """
    def __init__(self):
        self.configs = load_bank_configs()

    def detect_bank_from_text(self, text: str) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Detects bank using IFSC regex or fuzzy bank name matching in statement headers.
        """
        if not text:
            return None, 0.0

        upper_text = text.upper()
        # 1. Search for IFSC regex: [A-Z]{4}0[A-Z0-9]{6}
        ifsc_matches = re.findall(r'\b([A-Z]{4})0[A-Z0-9]{6}\b', upper_text)
        if ifsc_matches:
            prefix = ifsc_matches[0]
            for cfg in self.configs:
                if prefix in cfg.get("ifsc_prefixes", []):
                    return cfg, 98.0

        # 2. Match bank name keywords
        for cfg in self.configs:
            bank_name = cfg.get("bank_name", "").upper()
            code = cfg.get("bank_code", "").upper()
            if bank_name in upper_text or code in upper_text:
                return cfg, 85.0

        # 3. Check for any known IFSC prefixes anywhere
        for cfg in self.configs:
            for pfx in cfg.get("ifsc_prefixes", []):
                if pfx in upper_text:
                    return cfg, 80.0

        return None, 30.0

    def match_header_columns(self, header_row: List[str], config: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        Maps column indices to standard fields: date, narration, ref, debit, credit, balance.
        """
        mapping = {}
        header_clean = [str(col).strip().upper() for col in header_row]

        aliases = {
            "date": ["DATE", "TXN DATE", "TRAN DATE", "TRANSACTION DATE", "POST DATE"],
            "value_date": ["VALUE DATE", "VALUE DT"],
            "narration": ["NARRATION", "DESCRIPTION", "PARTICULARS", "TRANSACTION DETAILS", "TRAN PARTICULARS"],
            "ref": ["REF", "CHQ/REF", "CHQ NO", "CHEQUE NO", "REF NO", "REFERENCE", "UTR", "CHQ / REF NO."],
            "debit": ["DEBIT", "WITHDRAWAL", "DR", "WITHDRAWAL (DR)", "WITHDRAWAL DR", "DEBIT AMOUNT"],
            "credit": ["CREDIT", "DEPOSIT", "CR", "DEPOSIT (CR)", "DEPOSIT CR", "DEPOSIT AMOUNT"],
            "balance": ["BALANCE", "CLOSING BALANCE", "RUNNING BALANCE", "NET BALANCE", "TOTAL BALANCE"]
        }

        if config and "header_aliases" in config:
            for key, custom_list in config["header_aliases"].items():
                aliases[key] = [c.upper() for c in custom_list] + aliases.get(key, [])

        for idx, col in enumerate(header_clean):
            for field, terms in aliases.items():
                if field not in mapping:
                    for term in terms:
                        if term == col or (len(term) > 3 and term in col):
                            mapping[field] = idx
                            break

        return mapping

    def parse_raw_rows(
        self,
        table_rows: List[List[str]],
        config: Optional[Dict[str, Any]] = None,
        source_page_no: int = 1
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parses raw extracted table rows into normalized transaction dicts.
        Handles multi-line wrapping and balance reconciliation.
        Returns (parsed_transactions, review_items).
        """
        if not table_rows:
            return [], []

        # Find header row
        header_idx = -1
        col_map = {}
        for i, row in enumerate(table_rows[:10]):
            col_map = self.match_header_columns(row, config)
            if "date" in col_map and ("debit" in col_map or "credit" in col_map) and "balance" in col_map:
                header_idx = i
                break

        if header_idx == -1:
            # Fallback column index search
            for i, row in enumerate(table_rows[:10]):
                col_map = self.match_header_columns(row, None)
                if "date" in col_map and "balance" in col_map:
                    header_idx = i
                    break

        if header_idx == -1:
            # Return raw row review item
            return [], [{
                "issue_type": "UNKNOWN_TABLE_HEADER",
                "confidence": 30.0,
                "suggested_value": {"raw_sample": table_rows[:3]},
                "source_page_no": source_page_no
            }]

        transactions = []
        review_items = []
        data_rows = table_rows[header_idx + 1:]

        from app.services.table_parse import parse_table_page_rows
        transactions, row_reviews, failed_count = parse_table_page_rows(
            data_rows, col_map, config, source_page_no
        )
        review_items.extend(row_reviews)

        # Balance validation check: prev_balance + credit - debit == balance (tolerance ₹1.00)
        for idx in range(1, len(transactions)):
            prev_bal = transactions[idx - 1]["balance"]
            cur_bal = transactions[idx]["balance"]
            expected_bal = prev_bal + transactions[idx]["credit"] - transactions[idx]["debit"]
            diff = abs(cur_bal - expected_bal)
            if diff > 1.05:  # Tolerance ₹1.00
                transactions[idx]["confidence"] = max(transactions[idx]["confidence"] - 25.0, 35.0)
                review_items.append({
                    "issue_type": "BALANCE_MISMATCH",
                    "confidence": transactions[idx]["confidence"],
                    "suggested_value": {
                        "expected_balance": round(expected_bal, 2),
                        "actual_balance": cur_bal,
                        "discrepancy": round(diff, 2),
                        "txn_date": str(transactions[idx]["txn_date"]),
                        "narration": transactions[idx]["narration_raw"]
                    },
                    "source_page_no": transactions[idx]["source_page_no"],
                    "narration_raw": transactions[idx]["narration_raw"],
                    "amount": transactions[idx]["debit"] or transactions[idx]["credit"],
                    "date": transactions[idx]["txn_date"]
                })

        return transactions, review_items

