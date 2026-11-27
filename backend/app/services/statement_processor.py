import os
import hashlib
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.core.encryption import encrypt_data, decrypt_data, encrypt_string, mask_account_number
from app.core.logging import logger
from app.core.errors import (
    PasswordRequiredException,
    InvalidPasswordException,
    CorruptedPdfException,
    UnsupportedEncryptionException,
    NoTransactionsFoundException,
    OcrExtractionFailedException,
)
from app.services.pdf_unlock import unlock_pdf_in_memory
from app.services.pdf_extract import extract_pdf_pages_data, extract_excel_or_csv
from app.services.bank_detect import detect_bank_and_account
from app.parsers.generic_parser import BankParserEngine
from app.services.narration import extract_channel_and_counterparty
from app.services.classify import classify_transaction
from app.services.confidence import compute_transaction_confidence, compute_file_confidence
from app.services.emi_detect import detect_emi_intelligence
from app.services.return_match import reconcile_returns_and_charges
from app.services.cross_account import reconcile_cross_account_transfers
from app.services.abb_calc import compute_monthly_abb_metrics
from app.services.turnover_calc import calculate_monthly_turnover_and_flows

from app.models.models import (
    Statement, Transaction, EmiRecord, EmiAttempt, ReturnRecord,
    MonthlySummary, AnalysisVersion, ReviewQueue, AuditLog, LoanApplication
)

parser_engine = BankParserEngine()

def process_statement_pipeline(
    statement_id: str,
    db: Session,
    pdf_password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Complete end-to-end processing pipeline for an uploaded bank statement.
    """
    stmt = db.query(Statement).filter(Statement.id == statement_id).first()
    if not stmt:
        raise ValueError(f"Statement {statement_id} not found")

    stmt.status = "PARSING"
    stmt.processing_stage = "PDF_VERIFICATION"
    db.commit()

    try:
        # 1. Read encrypted file from disk and decrypt in memory
        with open(stmt.file_path_encrypted, "rb") as f:
            encrypted_bytes = f.read()
        raw_bytes = decrypt_data(encrypted_bytes)

        ext = stmt.file_name_original.lower().split(".")[-1]
        pages_data = []
        used_ocr = False

        if ext == "pdf":
            # Unlock PDF in memory
            stmt.processing_stage = "DOCUMENT_UNLOCKING"
            db.commit()
            doc, was_encrypted = unlock_pdf_in_memory(raw_bytes, pdf_password)
            if was_encrypted:
                stmt.status = "PASSWORD_VERIFIED"
                stmt.processing_stage = "TRANSACTION_EXTRACTION"
                stmt.error_message = None
                db.commit()
            stmt.page_count = len(doc)
            stmt.processing_stage = "TRANSACTION_EXTRACTION"
            db.commit()
            pages_data, used_ocr = extract_pdf_pages_data(doc, raw_bytes, pdf_password)
            doc.close()
        elif ext in ["xlsx", "xls", "csv"]:
            stmt.page_count = 1
            stmt.processing_stage = "TRANSACTION_EXTRACTION"
            db.commit()
            pages_data = extract_excel_or_csv(raw_bytes, stmt.file_name_original)
        else:
            raise CorruptedPdfException(f"Unsupported file format: {ext}")

        # 2. Bank and account detection across full text
        full_text = " ".join([p.get("text", "") for p in pages_data])
        if used_ocr and len(full_text.strip()) < 20:
            raise OcrExtractionFailedException("Scanned PDF OCR extraction failed or returned no readable text.")
        bank_meta = detect_bank_and_account(full_text)

        stmt.bank_name = bank_meta["bank_name"]
        stmt.bank_detect_confidence = bank_meta["bank_detect_confidence"]
        stmt.account_type = bank_meta["account_type"]
        if bank_meta["ifsc"]:
            stmt.ifsc = bank_meta["ifsc"]
        if bank_meta["branch"]:
            stmt.branch = bank_meta["branch"]

        raw_acc_no = bank_meta["account_no"] or "1000000000"
        stmt.account_no_masked = mask_account_number(raw_acc_no)
        stmt.account_no_encrypted = encrypt_string(raw_acc_no)

        # Update customer details if extracted from statement
        app_obj = db.query(LoanApplication).filter(LoanApplication.id == stmt.application_id).first()
        if app_obj and app_obj.customer and bank_meta.get("customer_name"):
            curr_name = app_obj.customer.name or ""
            if curr_name in ["Applicant", "Applicant One", "New Customer", ""] or "Applicant" in curr_name:
                app_obj.customer.name = bank_meta["customer_name"]
                db.flush()

        # 3. Parse transactions page by page using bank config
        stmt.processing_stage = "TRANSACTION_CATEGORIZATION"
        db.commit()
        all_transactions = []
        all_review_items = []
        failed_rows_count = 0

        bank_cfg = bank_meta.get("config")

        for page in pages_data:
            page_no = page["page_no"]
            table_rows = page.get("table_rows", [])
            txns, revs = parser_engine.parse_raw_rows(table_rows, bank_cfg, source_page_no=page_no)

            for t in txns:
                try:
                    # Channel and Counterparty extraction (counterparty is always Optional)
                    meta = extract_channel_and_counterparty(t.get("narration_raw", ""))
                    t["channel"] = meta.get("channel", "OTHER")
                    t["counterparty"] = meta.get("counterparty")  # Optional[str] = None
                    t["ref_no"] = meta.get("ref_no") or t.get("ref_no")
                    t["utr"] = meta.get("ref_no") or t.get("utr")

                    # Category classification
                    t["category"] = classify_transaction(
                        t.get("narration_raw", ""),
                        float(t.get("debit", 0.0)),
                        float(t.get("credit", 0.0)),
                        t["channel"]
                    )

                    # Confidence calculation
                    has_mismatch = any(r.get("source_page_no") == page_no and r.get("issue_type") == "BALANCE_MISMATCH" for r in revs)
                    conf = compute_transaction_confidence(
                        t,
                        bank_detected=(stmt.bank_detect_confidence >= 70.0),
                        used_ocr=used_ocr,
                        has_balance_mismatch=has_mismatch
                    )

                    # If counterparty cannot be extracted and not Opening Balance/tax/charges/cash: confidence -= 10
                    if not t["counterparty"] and t["category"] not in ["OPENING_BALANCE", "TAX", "BANK_CHARGES", "CASH_DEPOSIT", "CASH_WITHDRAWAL"]:
                        conf = max(conf - 10.0, 10.0)

                    t["confidence"] = conf
                    all_transactions.append(t)

                except Exception as row_err:
                    failed_rows_count += 1
                    logger.error(
                        "Row parse failed",
                        extra={
                            "page": page_no,
                            "narration_raw": t.get("narration_raw", ""),
                            "error": str(row_err)
                        }
                    )
                    all_review_items.append({
                        "issue_type": "ROW_PARSE_ERROR",
                        "confidence": 30.0,
                        "suggested_value": {"narration": t.get("narration_raw", ""), "error": str(row_err)},
                        "source_page_no": page_no,
                        "narration_raw": t.get("narration_raw", "Unparsed row")
                    })

            all_review_items.extend(revs)

        # If duplicate transactions across pages or files, flag them and do not create duplicates
        seen_hashes = set()
        unique_transactions = []
        for t in all_transactions:
            if t["row_hash"] in seen_hashes:
                t["is_duplicate"] = True
            else:
                seen_hashes.add(t["row_hash"])
                unique_transactions.append(t)
        all_transactions = unique_transactions

        # Fail explicitly if NO transactions were extracted (prevents misleading zero-value dashboard)
        if not all_transactions:
            raise NoTransactionsFoundException(
                "Statement could not be parsed. Please check the PDF password, file quality or statement format."
            )

        # Determine period
        dates = [t["txn_date"] for t in all_transactions]
        stmt.period_from = min(dates)
        stmt.period_to = max(dates)

        # Statement-level Balance Reconciliation (chronological order)
        chrono_txns = list(all_transactions)
        if len(chrono_txns) >= 2 and chrono_txns[0]["txn_date"] > chrono_txns[-1]["txn_date"]:
            chrono_txns = list(reversed(chrono_txns))

        first_txn = chrono_txns[0]
        last_txn = chrono_txns[-1]

        if first_txn.get("category") == "OPENING_BALANCE":
            opening_balance = round(float(first_txn["balance"]), 2)
            flow_txns = chrono_txns[1:]
        else:
            opening_balance = round(float(first_txn["balance"]) - float(first_txn["credit"]) + float(first_txn["debit"]), 2)
            flow_txns = chrono_txns

        total_credits = round(sum(float(t["credit"]) for t in flow_txns), 2)
        total_debits = round(sum(float(t["debit"]) for t in flow_txns), 2)
        closing_balance = round(float(last_txn["balance"]), 2)
        expected_closing_balance = round(opening_balance + total_credits - total_debits, 2)
        reconciliation_diff = round(closing_balance - expected_closing_balance, 2)

        if abs(reconciliation_diff) <= 1.05:
            reconciliation_status = "MATCHED"
        else:
            reconciliation_status = "MISMATCH"
            all_review_items.append({
                "issue_type": "BALANCE_RECONCILIATION_MISMATCH",
                "confidence": 45.0,
                "suggested_value": {
                    "opening_balance": opening_balance,
                    "total_credits": total_credits,
                    "total_debits": total_debits,
                    "expected_closing_balance": expected_closing_balance,
                    "actual_closing_balance": closing_balance,
                    "discrepancy": reconciliation_diff
                },
                "source_page_no": last_txn.get("source_page_no", 1),
                "narration_raw": f"Statement balance reconciliation mismatch: expected {expected_closing_balance}, extracted {closing_balance} (diff {reconciliation_diff})"
            })

        stmt.opening_balance = opening_balance
        stmt.closing_balance = closing_balance
        stmt.expected_closing_balance = expected_closing_balance
        stmt.reconciliation_diff = reconciliation_diff
        stmt.reconciliation_status = reconciliation_status
        stmt.total_credits = total_credits
        stmt.total_debits = total_debits

        # 4. Save Transactions into DB
        # Delete previous unversioned transactions for this statement if re-parsing
        db.query(Transaction).filter(Transaction.statement_id == stmt.id).delete()
        db_transactions = []
        for t in all_transactions:
            try:
                db_txn = Transaction(
                    statement_id=stmt.id,
                    application_id=stmt.application_id,
                    txn_date=t["txn_date"],
                    value_date=t.get("value_date"),
                    narration_raw=t["narration_raw"],
                    narration_clean=t.get("narration_clean"),
                    ref_no=t.get("ref_no"),
                    utr=t.get("utr"),
                    debit=t.get("debit", 0.0),
                    credit=t.get("credit", 0.0),
                    balance=t["balance"],
                    channel=t.get("channel", "OTHER"),
                    counterparty=t.get("counterparty"),  # Optional, can be None
                    category=t.get("category", "UNCATEGORIZED"),
                    confidence=t.get("confidence", 100.0),
                    source_page_no=t.get("source_page_no", 1),
                    row_hash=t["row_hash"],
                    is_duplicate=t.get("is_duplicate", False),
                    is_internal_transfer=t.get("is_internal_transfer", False)
                )
                db.add(db_txn)
                db_transactions.append((db_txn, t))
            except Exception as insert_err:
                failed_rows_count += 1
                logger.error(
                    "Transaction DB insert failed",
                    extra={
                        "page": t.get("source_page_no", 1),
                        "narration_raw": t.get("narration_raw", ""),
                        "error": str(insert_err)
                    }
                )
        db.commit()

        # Update IDs in memory objects
        for db_txn, mem_txn in db_transactions:
            mem_txn["id"] = db_txn.id

        # 5. EMI Intelligence Detection & Banking Analysis
        stmt.processing_stage = "BANKING_ANALYSIS"
        db.commit()
        confirmed_emis, possible_emis, emi_attempts = detect_emi_intelligence(all_transactions)

        # 6. Return Reconciliation
        return_records, return_revs = reconcile_returns_and_charges(all_transactions, emi_attempts)
        all_review_items.extend(return_revs)

        # 7. Cross-Account Reconciliation
        other_stmts = db.query(Statement).filter(
            Statement.application_id == stmt.application_id,
            Statement.id != stmt.id
        ).all()

        if other_stmts:
            all_account_txns = {stmt.id: all_transactions}
            for other in other_stmts:
                other_db_txns = db.query(Transaction).filter(Transaction.statement_id == other.id).all()
                all_account_txns[other.id] = [
                    {
                        "id": o.id, "txn_date": o.txn_date, "narration_raw": o.narration_raw,
                        "debit": float(o.debit), "credit": float(o.credit), "balance": float(o.balance),
                        "source_page_no": o.source_page_no
                    } for o in other_db_txns
                ]
            app_obj = db.query(LoanApplication).filter(LoanApplication.id == stmt.application_id).first()
            cust_name = app_obj.customer.name if (app_obj and app_obj.customer) else ""
            confirmed_transfers, transfer_revs = reconcile_cross_account_transfers(all_account_txns, cust_name)
            all_review_items.extend(transfer_revs)

            # Update DB for internal transfers
            for t_a, t_b in confirmed_transfers:
                db.query(Transaction).filter(Transaction.id == t_a.get("id")).update({
                    "is_internal_transfer": True,
                    "internal_match_id": t_a.get("internal_match_id")
                })
                db.query(Transaction).filter(Transaction.id == t_b.get("id")).update({
                    "is_internal_transfer": True,
                    "internal_match_id": t_b.get("internal_match_id")
                })
            db.commit()

        # 8. Store EMI Records & Attempts into DB
        for group_key, emi_data in confirmed_emis:
            db_emi = EmiRecord(
                application_id=stmt.application_id,
                lender_name=emi_data["lender_name"],
                lender_confidence=emi_data["lender_confidence"],
                mandate_ref=emi_data["mandate_ref"],
                amount=emi_data["amount"],
                frequency=emi_data["frequency"],
                first_date=emi_data["first_date"],
                last_date=emi_data["last_date"],
                total_attempts=emi_data["total_attempts"],
                total_success=sum(1 for a in emi_attempts if a.get("group_key") == group_key and a.get("status") == "SUCCESS"),
                total_returns=sum(1 for a in emi_attempts if a.get("group_key") == group_key and a.get("status") == "RETURNED"),
                status="ACTIVE"
            )
            db.add(db_emi)
            db.flush()

            for att in emi_attempts:
                if att.get("group_key") == group_key and att.get("transaction_id"):
                    db_att = EmiAttempt(
                        emi_record_id=db_emi.id,
                        transaction_id=att["transaction_id"],
                        attempt_date=att["attempt_date"],
                        amount=att["amount"],
                        status=att["status"]
                    )
                    db.add(db_att)

        # Store Return Records
        for ret in return_records:
            db_ret = ReturnRecord(
                application_id=stmt.application_id,
                emi_attempt_id=ret.get("emi_attempt_id"),
                original_txn_id=ret.get("original_txn_id"),
                return_txn_id=ret["return_txn_id"],
                return_date=ret["return_date"],
                return_amount=ret["return_amount"],
                return_charge_amount=ret["return_charge_amount"],
                charge_txn_id=ret.get("charge_txn_id"),
                reason=ret["reason"],
                recovery_status=ret["recovery_status"],
                recovery_txn_id=ret.get("recovery_txn_id")
            )
            db.add(db_ret)
        db.commit()

        # 9. Compute Monthly ABB & Turnover metrics
        abb_metrics = compute_monthly_abb_metrics(all_transactions, stmt.account_type)
        turnover_metrics = calculate_monthly_turnover_and_flows(all_transactions, emi_attempts)

        # Combine into monthly summaries
        turnover_by_month = {m["month"]: m for m in turnover_metrics}
        db.query(MonthlySummary).filter(
            MonthlySummary.application_id == stmt.application_id,
            MonthlySummary.account_id == stmt.id
        ).delete()

        monthly_summaries = []
        for abb in abb_metrics:
            m_str = abb["month"]
            t_m = turnover_by_month.get(m_str, {})
            ms = MonthlySummary(
                application_id=stmt.application_id,
                account_id=stmt.id,
                month=m_str,
                gross_credit=t_m.get("gross_credit", 0.0),
                business_turnover=t_m.get("business_turnover", 0.0),
                non_business_credit=t_m.get("non_business_credit", 0.0),
                internal_transfer_credit_excluded=t_m.get("internal_transfer_credit_excluded", 0.0),
                total_debit=t_m.get("total_debit", 0.0),
                net_flow=t_m.get("net_flow", 0.0),
                abb=abb["abb"],
                min_balance=abb["min_balance"],
                max_balance=abb["max_balance"],
                min_balance_date=abb["min_balance_date"],
                month_end_balance=abb["month_end_balance"],
                negative_days=abb["negative_days"],
                days_below_5000=abb["days_below_5000"],
                days_below_10000=abb["days_below_10000"],
                emi_burden=t_m.get("emi_burden", 0.0),
                emi_bounce_count=t_m.get("emi_bounce_count", 0)
            )
            db.add(ms)
            monthly_summaries.append(ms)
        db.commit()

        # 10. Review Queue items insertion (for low confidence or unparsed or mismatches)
        for rev in all_review_items:
            rq = ReviewQueue(
                application_id=stmt.application_id,
                statement_id=stmt.id,
                issue_type=rev["issue_type"],
                confidence=rev["confidence"],
                suggested_value=rev.get("suggested_value"),
                status="OPEN"
            )
            db.add(rq)
        db.commit()

        # 11. Analysis Versioning (PART 3: Never overwrite history, create new version)
        current_version_count = db.query(AnalysisVersion).filter(
            AnalysisVersion.application_id == stmt.application_id
        ).count()
        new_version_no = current_version_count + 1

        # Mark previous versions is_current = False
        db.query(AnalysisVersion).filter(
            AnalysisVersion.application_id == stmt.application_id
        ).update({"is_current": False})

        file_confidence = compute_file_confidence(
            all_transactions,
            len(all_review_items),
            stmt.bank_detect_confidence,
            used_ocr
        )

        version_summary = {
            "version_no": new_version_no,
            "statement_id": stmt.id,
            "bank_name": stmt.bank_name,
            "rows_parsed": len(all_transactions),
            "failed_rows_count": failed_rows_count,
            "file_confidence": float(file_confidence),
            "total_turnover": round(sum(float(m.business_turnover) for m in monthly_summaries), 2),
            "avg_abb": round(sum(float(m.abb) for m in monthly_summaries) / max(len(monthly_summaries), 1), 2),
            "emi_count": len(confirmed_emis),
            "return_count": len(return_records),
            "review_queue_count": len(all_review_items)
        }

        analysis_ver = AnalysisVersion(
            application_id=stmt.application_id,
            version_no=new_version_no,
            summary_json=version_summary,
            created_by=stmt.uploaded_by,
            is_current=True
        )
        db.add(analysis_ver)

        # Audit Log
        audit = AuditLog(
            user_id=stmt.uploaded_by,
            action="PARSE_COMPLETED",
            entity="Statement",
            entity_id=stmt.id,
            old_value=None,
            new_value={"version_no": new_version_no, "rows": len(all_transactions), "failed_rows": failed_rows_count, "confidence": file_confidence}
        )
        db.add(audit)

        has_warnings = (
            reconciliation_status == "MISMATCH"
            or len(all_review_items) > 0
            or failed_rows_count > 0
        )
        stmt.status = "PARSED_WITH_WARNINGS" if has_warnings else "PARSED"
        stmt.processing_stage = "ANALYSIS_COMPLETED"
        stmt.error_message = (
            f"Balance reconciliation mismatch of {reconciliation_diff} detected."
            if reconciliation_status == "MISMATCH"
            else None
        )
        db.commit()

        return {
            "statement_id": stmt.id,
            "status": stmt.status,
            "bank_name": stmt.bank_name,
            "bank_confidence": stmt.bank_detect_confidence,
            "rows_parsed": len(all_transactions),
            "failed_rows_count": failed_rows_count,
            "file_confidence": file_confidence,
            "review_queue_count": len(all_review_items),
            "opening_balance": opening_balance,
            "closing_balance": closing_balance,
            "expected_closing_balance": expected_closing_balance,
            "reconciliation_diff": reconciliation_diff,
            "reconciliation_status": reconciliation_status,
            "total_credits": total_credits,
            "total_debits": total_debits,
            "version_no": new_version_no
        }

    except (PasswordRequiredException, InvalidPasswordException) as pwd_err:
        db.rollback()
        stmt.status = "PASSWORD_REQUIRED"
        stmt.reconciliation_status = "UNAVAILABLE"
        stmt.error_message = pwd_err.message if hasattr(pwd_err, 'message') else str(pwd_err)
        db.commit()
        logger.warning(f"Statement {stmt.id} requires password: {stmt.error_message}")
        raise
    except (CorruptedPdfException, UnsupportedEncryptionException) as file_err:
        db.rollback()
        stmt.status = "INVALID_FILE"
        stmt.reconciliation_status = "UNAVAILABLE"
        stmt.error_message = file_err.message if hasattr(file_err, 'message') else str(file_err)
        db.commit()
        logger.warning(f"Statement {stmt.id} invalid file: {stmt.error_message}")
        raise
    except (NoTransactionsFoundException, OcrExtractionFailedException) as parse_err:
        db.rollback()
        stmt.status = "PARSING_FAILED"
        stmt.reconciliation_status = "UNAVAILABLE"
        stmt.error_message = parse_err.message if hasattr(parse_err, 'message') else str(parse_err)
        db.commit()
        logger.warning(f"Statement {stmt.id} parsing failed: {stmt.error_message}")
        raise
    except Exception as e:
        db.rollback()
        stmt.status = "PARSING_FAILED"
        stmt.reconciliation_status = "UNAVAILABLE"
        stmt.error_message = str(e)
        db.commit()
        logger.error(f"Error parsing statement {stmt.id}: {str(e)}", exc_info=True)
        raise

