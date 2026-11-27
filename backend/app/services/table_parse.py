import re
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, date

from app.core.logging import logger
from app.parsers.generic_parser import parse_indian_amount, parse_date_string

def parse_table_page_rows(
    table_rows: List[List[str]],
    col_map: Dict[str, int],
    config: Optional[Dict[str, Any]] = None,
    source_page_no: int = 1
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """
    Parses table rows for a single page with per-row try/except isolation.
    If ONE row fails:
      - Log error with page number and narration_raw
      - Add to review queue
      - Continues parsing subsequent rows
    Returns: (parsed_transactions, review_items, failed_rows_count)
    """
    if not table_rows or not col_map:
        return [], [], 0

    transactions = []
    review_items = []
    failed_rows_count = 0

    date_formats = config.get("date_formats", []) if config else []
    opening_keywords = config.get("opening_keywords", ["OPENING", "B/F", "BROUGHT FORWARD"]) if config else ["OPENING", "B/F"]

    i = 0
    while i < len(table_rows):
        row = table_rows[i]
        if not any(row):
            i += 1
            continue

        raw_narration_preview = ""
        try:
            date_val = str(row[col_map["date"]]).strip() if "date" in col_map and col_map["date"] < len(row) else ""
            parsed_date = parse_date_string(date_val, date_formats)

            if not parsed_date:
                # Skip page headers/footers before treating as continuation text
                row_text_upper = " ".join([str(c).strip().upper() for c in row if c])
                is_header_footer = (
                    any(k in row_text_upper for k in [
                        "STATEMENT OF ACCOUNT", "GENERATED ON", "BROUGHT FORWARD",
                        "CARRIED FORWARD", "PAGE ", "OPENING BALANCE", "CLOSING BALANCE",
                        "TOTAL DEBIT", "TOTAL CREDIT"
                    ])
                    or ("DATE" in row_text_upper and "BALANCE" in row_text_upper and ("DEBIT" in row_text_upper or "WITHDRAWAL" in row_text_upper or "NARRATION" in row_text_upper))
                )
                if not is_header_footer and transactions and len(row) > col_map.get("narration", -1):
                    continuation_text = " ".join([str(c).strip() for c in row if c])
                    if continuation_text:
                        transactions[-1]["narration_raw"] += " " + continuation_text
                        transactions[-1]["narration_clean"] = re.sub(r'\s+', ' ', transactions[-1]["narration_raw"]).strip()
                i += 1
                continue

            narration = str(row[col_map["narration"]]).strip() if "narration" in col_map and col_map["narration"] < len(row) else ""
            raw_narration_preview = narration
            ref = str(row[col_map["ref"]]).strip() if "ref" in col_map and col_map["ref"] < len(row) else None
            if ref == "-" or ref == "—" or not ref:
                ref = None

            debit_raw = row[col_map["debit"]] if "debit" in col_map and col_map["debit"] < len(row) else None
            credit_raw = row[col_map["credit"]] if "credit" in col_map and col_map["credit"] < len(row) else None
            balance_raw = row[col_map["balance"]] if "balance" in col_map and col_map["balance"] < len(row) else None

            # Multi-line narration wrap check
            j = i + 1
            while j < len(table_rows):
                next_row = table_rows[j]
                next_date_val = str(next_row[col_map["date"]]).strip() if "date" in col_map and col_map["date"] < len(next_row) else ""
                if parse_date_string(next_date_val, date_formats):
                    break
                extra_narr = str(next_row[col_map.get("narration", 0)]).strip() if len(next_row) > col_map.get("narration", 0) else ""
                if extra_narr:
                    narration += " " + extra_narr
                j += 1
            i = j - 1

            debit = abs(parse_indian_amount(debit_raw) or 0.0)
            credit = abs(parse_indian_amount(credit_raw) or 0.0)
            balance = parse_indian_amount(balance_raw)

            # Check if this is an Opening Balance row
            is_opening = any(k in narration.upper() for k in opening_keywords)

            if balance is None:
                # Flag missing balance
                review_items.append({
                    "issue_type": "MISSING_BALANCE",
                    "confidence": 40.0,
                    "suggested_value": {"row": row, "date": str(parsed_date)},
                    "source_page_no": source_page_no,
                    "narration_raw": narration
                })
                i += 1
                continue

            row_hash_str = f"{parsed_date}_{debit}_{credit}_{balance}_{ref or ''}_{narration[:30]}"
            row_hash = hashlib.sha256(row_hash_str.encode("utf-8")).hexdigest()

            txn_obj = {
                "txn_date": parsed_date,
                "value_date": parsed_date,
                "narration_raw": narration,
                "narration_clean": re.sub(r'\s+', ' ', narration).strip(),
                "ref_no": ref,
                "utr": ref,
                "debit": debit,
                "credit": credit,
                "balance": balance,
                "channel": "OTHER",
                "counterparty": None,  # Optional, default None
                "category": "OPENING_BALANCE" if is_opening else "UNCATEGORIZED",
                "source_page_no": source_page_no,
                "row_hash": row_hash,
                "confidence": 100.0,
                "is_duplicate": False,
                "is_internal_transfer": False
            }
            transactions.append(txn_obj)

        except Exception as row_err:
            failed_rows_count += 1
            logger.error(
                "Row parse failed",
                extra={
                    "page": source_page_no,
                    "narration_raw": raw_narration_preview or " ".join([str(c) for c in row]),
                    "error": str(row_err)
                }
            )
            review_items.append({
                "issue_type": "ROW_PARSE_ERROR",
                "confidence": 25.0,
                "suggested_value": {
                    "raw_row": row,
                    "error": str(row_err)
                },
                "source_page_no": source_page_no,
                "narration_raw": raw_narration_preview or "Unparsed row format"
            })

        i += 1

    return transactions, review_items, failed_rows_count

