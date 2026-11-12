from typing import Dict, Any, List

def compute_transaction_confidence(
    txn: Dict[str, Any],
    bank_detected: bool,
    used_ocr: bool,
    has_balance_mismatch: bool
) -> float:
    """
    Computes confidence score (0-100) for an individual transaction row.
    Rules:
      - Start at 100
      - If OCR file: cap at 75
      - If unknown bank: cap at 50
      - Balance mismatch: -20
      - Missing ref/UTR: -10
    """
    score = 100.0
    if not txn.get("ref_no") and not txn.get("utr"):
        score -= 10.0

    if has_balance_mismatch:
        score -= 20.0

    if not bank_detected:
        score = min(score, 50.0)

    if used_ocr:
        score = min(score, 75.0)

    return max(round(score, 1), 10.0)

def compute_file_confidence(
    transactions: List[Dict[str, Any]],
    review_queue_count: int,
    bank_confidence: float,
    used_ocr: bool
) -> float:
    """
    Calculates overall statement parse confidence.
    """
    if not transactions:
        return 0.0

    avg_txn_conf = sum(t.get("confidence", 80.0) for t in transactions) / len(transactions)
    overall = (avg_txn_conf * 0.6) + (bank_confidence * 0.4)

    if used_ocr:
        overall = min(overall, 75.0)

    if review_queue_count > 0:
        penalty = min(review_queue_count * 2.0, 30.0)
        overall -= penalty

    return max(round(overall, 1), 20.0)

