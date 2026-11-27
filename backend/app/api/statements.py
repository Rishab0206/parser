import os
import hashlib
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_current_user, require_roles, CurrentUser, Role
from app.core.encryption import encrypt_data
from app.core.errors import (
    PasswordRequiredException,
    InvalidPasswordException,
    CorruptedPdfException,
    UnsupportedEncryptionException,
    NoTransactionsFoundException,
    OcrExtractionFailedException,
)
from app.models.models import Statement, LoanApplication, Customer, AuditLog
from app.schemas.schemas import StatementStatusResponse
from app.services.statement_processor import process_statement_pipeline
from app.services.pdf_unlock import inspect_pdf_bytes
from app.core.logging import logger

router = APIRouter(prefix="/api/statements", tags=["Statements"])

@router.post("/inspect")
async def inspect_statement_file(
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_roles([Role.ADMIN, Role.UNDERWRITER, Role.SALES_DSA]))
):
    """
    Immediately inspects an uploaded file (PDF/CSV/XLS/XLSX) before parsing.
    Detects encryption, corrupted PDFs, scanned/image PDFs, and extractable text.
    """
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > 50:
        raise HTTPException(status_code=400, detail="File size exceeds maximum allowed limit of 50MB")

    ext = file.filename.lower().split(".")[-1] if file.filename and "." in file.filename else ""
    if ext not in ["pdf", "csv", "xls", "xlsx"]:
        return {
            "is_valid": False,
            "is_encrypted": False,
            "is_scanned": False,
            "has_extractable_text": False,
            "page_count": 0,
            "file_status": "INVALID_FILE",
            "classification": "UNSUPPORTED_FORMAT",
            "message": "Unsupported file format. Please upload PDF, CSV, XLS, or XLSX."
        }

    if ext == "pdf":
        return inspect_pdf_bytes(content)

    return {
        "is_valid": True,
        "is_encrypted": False,
        "is_scanned": False,
        "has_extractable_text": True,
        "page_count": 1,
        "file_status": "FILE_UPLOADED",
        "classification": "TABULAR_SPREADSHEET",
        "message": "No password required. Spreadsheet ready to parse."
    }

@router.post("/upload")
async def upload_statement(
    file: UploadFile = File(...),
    application_id: Optional[str] = Form(None),
    customer_name: Optional[str] = Form(None),
    pdf_password: Optional[str] = Form(None),
    account_type: Optional[str] = Form("SAVINGS"),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles([Role.ADMIN, Role.UNDERWRITER, Role.SALES_DSA]))
):
    """
    Uploads bank statement file (PDF/CSV/XLS/XLSX <= 50MB).
    Encrypts file at rest with AES-256.
    Computes SHA-256 hash for deduplication.
    Never persists pdf_password to disk, database, or logs.
    """
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    if file_size_mb > 50:
        raise HTTPException(status_code=400, detail="File size exceeds maximum allowed limit of 50MB")

    # Validate file extension
    ext = file.filename.lower().split(".")[-1] if file.filename and "." in file.filename else ""
    if ext not in ["pdf", "csv", "xls", "xlsx"]:
        raise HTTPException(status_code=400, detail="Unsupported file format. Please upload PDF, CSV, XLS, or XLSX.")

    # Backend is the source of truth: inspect PDF encryption & validity immediately
    pdf_inspection = None
    if ext == "pdf":
        pdf_inspection = inspect_pdf_bytes(content)
        if not pdf_inspection["is_valid"]:
            raise CorruptedPdfException(pdf_inspection["message"])

    # Deduplication check via SHA-256
    file_hash = hashlib.sha256(content).hexdigest()
    if application_id and application_id != "new":
        existing_stmt = db.query(Statement).filter(
            Statement.application_id == application_id,
            Statement.file_hash_sha256 == file_hash
        ).first()

        if existing_stmt:
            # If statement previously required a password or failed, and user is providing password or re-uploading
            if (existing_stmt.status in ["PASSWORD_REQUIRED", "FAILED", "PARSING_FAILED", "INVALID_FILE"] or pdf_password) and existing_stmt.status != "PARSED":
                logger.info(f"Re-processing existing statement {existing_stmt.id} with new password/attempt")
                if pdf_inspection and pdf_inspection["is_encrypted"] and not (pdf_password and pdf_password.strip()):
                    existing_stmt.status = "PASSWORD_REQUIRED"
                    existing_stmt.error_message = "PDF is password protected. Please enter the PDF password to unlock and parse."
                    db.commit()
                    return {
                        "statement_id": existing_stmt.id,
                        "application_id": existing_stmt.application_id,
                        "status": "PASSWORD_REQUIRED",
                        "is_encrypted": True,
                        "error_message": existing_stmt.error_message,
                        "file_name": existing_stmt.file_name_original,
                        "is_duplicate": False
                    }
                try:
                    process_statement_pipeline(existing_stmt.id, db, pdf_password)
                except (PasswordRequiredException, InvalidPasswordException) as pwd_err:
                    logger.warning(f"Password required on re-process: {pwd_err}")
                except Exception as p_err:
                    logger.warning(f"Re-process attempt failed: {p_err}")
                db.refresh(existing_stmt)
                return {
                    "statement_id": existing_stmt.id,
                    "application_id": existing_stmt.application_id,
                    "status": existing_stmt.status,
                    "is_encrypted": bool(pdf_inspection and pdf_inspection["is_encrypted"]),
                    "error_message": existing_stmt.error_message,
                    "file_name": existing_stmt.file_name_original,
                    "is_duplicate": False
                }
            return {
                "statement_id": existing_stmt.id,
                "application_id": existing_stmt.application_id,
                "status": existing_stmt.status,
                "message": "File with identical hash already uploaded for this application.",
                "is_duplicate": True
            }

    # Encrypt file at rest
    encrypted_bytes = encrypt_data(content)
    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    encrypted_filename = f"{file_hash}.enc"
    encrypted_filepath = os.path.join(settings.STORAGE_PATH, encrypted_filename)

    with open(encrypted_filepath, "wb") as f:
        f.write(encrypted_bytes)

    # Ensure application exists or create new for this customer
    app_obj = None
    if application_id and application_id != "new":
        app_obj = db.query(LoanApplication).filter(LoanApplication.id == application_id).first()

    if not app_obj:
        init_name = customer_name.strip() if (customer_name and customer_name.strip()) else "Applicant"
        cust = Customer(name=init_name, phone_masked="98XXX XXXXX")
        db.add(cust)
        db.flush()
        app_obj = LoanApplication(customer_id=cust.id, owner_user_id=current_user.user_id, status="ACTIVE")
        db.add(app_obj)
        db.flush()
        application_id = app_obj.id
    else:
        # Check ownership
        if not app_obj.owner_user_id:
            app_obj.owner_user_id = current_user.user_id
        elif current_user.role != Role.ADMIN and app_obj.owner_user_id != current_user.user_id:
            raise HTTPException(
                status_code=403,
                detail="Forbidden: You cannot upload statements to another user's customer."
            )

    is_encrypted_no_pwd = bool(pdf_inspection and pdf_inspection["is_encrypted"] and not (pdf_password and pdf_password.strip()))
    initial_status = "PASSWORD_REQUIRED" if is_encrypted_no_pwd else "FILE_UPLOADED"
    initial_err = "PDF is password protected. Please enter the PDF password to unlock and parse." if is_encrypted_no_pwd else None

    new_stmt = Statement(
        application_id=app_obj.id,
        owner_user_id=current_user.user_id,
        file_name_original=file.filename,
        file_hash_sha256=file_hash,
        file_path_encrypted=encrypted_filepath,
        account_type=account_type or "SAVINGS",
        page_count=pdf_inspection["page_count"] if pdf_inspection else 1,
        status=initial_status,
        error_message=initial_err,
        uploaded_by=current_user.username
    )
    db.add(new_stmt)
    db.commit()
    db.refresh(new_stmt)

    # Audit log
    audit = AuditLog(
        user_id=current_user.user_id,
        action="STATEMENT_UPLOADED",
        entity="Statement",
        entity_id=new_stmt.id,
        old_value=None,
        new_value={"file_name": file.filename, "size_mb": round(file_size_mb, 2), "is_encrypted": is_encrypted_no_pwd}
    )
    db.add(audit)
    db.commit()

    # If encrypted and no password provided, return immediately so UI prompts for password
    if is_encrypted_no_pwd:
        db.refresh(app_obj)
        return {
            "statement_id": new_stmt.id,
            "application_id": app_obj.id,
            "customer_name": app_obj.customer.name if app_obj.customer else "Applicant",
            "status": "PASSWORD_REQUIRED",
            "is_encrypted": True,
            "error_message": initial_err,
            "file_name": file.filename
        }

    # Trigger parsing pipeline: try async via Celery or background task
    try:
        from app.workers.parse_task import parse_statement_async
        parse_statement_async.delay(new_stmt.id, pdf_password)
    except Exception as e:
        logger.info(f"Celery queue not reachable ({e}), executing synchronously or via BackgroundTasks")
        try:
            process_statement_pipeline(new_stmt.id, db, pdf_password)
        except (PasswordRequiredException, InvalidPasswordException) as pwd_err:
            logger.warning(f"Password required for statement {new_stmt.id}: {pwd_err}")
        except (CorruptedPdfException, UnsupportedEncryptionException, NoTransactionsFoundException, OcrExtractionFailedException) as parse_err:
            logger.warning(f"Parsing failed for statement {new_stmt.id}: {parse_err}")
        except Exception as parse_err:
            logger.error(f"Sync parsing error: {parse_err}")

    db.refresh(new_stmt)
    db.refresh(app_obj)
    return {
        "statement_id": new_stmt.id,
        "application_id": app_obj.id,
        "customer_name": app_obj.customer.name if app_obj.customer else "Applicant",
        "status": new_stmt.status,
        "is_encrypted": bool(pdf_inspection and pdf_inspection["is_encrypted"]),
        "error_message": new_stmt.error_message,
        "file_name": file.filename
    }

@router.get("/{statement_id}/status")
def get_statement_status(
    statement_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    stmt = db.query(Statement).filter(Statement.id == statement_id).first()
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")

    if current_user.role != Role.ADMIN and stmt.owner_user_id and stmt.owner_user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this statement.")

    from app.models.models import Transaction, ReviewQueue
    rows_parsed = db.query(Transaction).filter(Transaction.statement_id == statement_id).count()
    open_reviews = db.query(ReviewQueue).filter(
        ReviewQueue.statement_id == statement_id,
        ReviewQueue.status == "OPEN"
    ).all()
    rq_count = len(open_reviews)
    failed_rows = [r for r in open_reviews if "ERROR" in r.issue_type]
    failed_rows_count = len(failed_rows)

    error_report = None
    if failed_rows_count > 0:
        error_report = {
            "failed_rows_count": failed_rows_count,
            "rows_parsed": rows_parsed,
            "errors": [
                {
                    "issue_type": r.issue_type,
                    "confidence": r.confidence,
                    "suggested_value": r.suggested_value,
                    "narration": r.suggested_value.get("narration") if isinstance(r.suggested_value, dict) else None
                } for r in failed_rows
            ]
        }

    cust_name = stmt.application.customer.name if (stmt.application and stmt.application.customer) else None

    return StatementStatusResponse(
        statement_id=stmt.id,
        status=stmt.status,
        bank_name=stmt.bank_name,
        bank_detect_confidence=stmt.bank_detect_confidence or 0.0,
        account_no_masked=stmt.account_no_masked,
        account_type=stmt.account_type,
        ifsc=stmt.ifsc,
        customer_name=cust_name,
        period_from=stmt.period_from,
        period_to=stmt.period_to,
        page_count=stmt.page_count,
        rows_parsed=rows_parsed,
        failed_rows_count=failed_rows_count,
        confidence=stmt.bank_detect_confidence or 0.0,
        review_queue_count=rq_count,
        opening_balance=stmt.opening_balance,
        closing_balance=stmt.closing_balance,
        expected_closing_balance=stmt.expected_closing_balance,
        reconciliation_diff=stmt.reconciliation_diff,
        reconciliation_status=stmt.reconciliation_status,
        total_credits=stmt.total_credits,
        total_debits=stmt.total_debits,
        error_message=stmt.error_message,
        error_report=error_report
    )

class UnlockStatementRequest(BaseModel):
    password: str

@router.post("/{statement_id}/unlock")
def unlock_statement_endpoint(
    statement_id: str,
    payload: UnlockStatementRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles([Role.ADMIN, Role.UNDERWRITER, Role.SALES_DSA]))
):
    """
    Unlocks a password-protected statement and runs the full analysis pipeline:
    - Decrypts and authenticates PDF with password
    - Bank & account metadata detection
    - Transaction parsing & confidence scoring
    - EMI detection & loan analysis
    - Return & bounce analysis (ACH/ECS)
    - Monthly ABB & turnover calculation
    - Customer history update
    Never stores or logs the password.
    """
    stmt = db.query(Statement).filter(Statement.id == statement_id).first()
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")

    if current_user.role != Role.ADMIN and stmt.owner_user_id and stmt.owner_user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this statement.")

    clean_pwd = payload.password.strip() if payload.password else ""
    if not clean_pwd:
        raise HTTPException(status_code=400, detail="Password cannot be empty. Please enter your account/PDF password.")

    try:
        result = process_statement_pipeline(statement_id, db, pdf_password=clean_pwd)
        db.refresh(stmt)
        cust_name = stmt.application.customer.name if (stmt.application and stmt.application.customer) else None
        return {
            "statement_id": stmt.id,
            "status": stmt.status,
            "bank_name": stmt.bank_name,
            "bank_confidence": stmt.bank_detect_confidence,
            "account_no_masked": stmt.account_no_masked,
            "account_type": stmt.account_type,
            "ifsc": stmt.ifsc,
            "customer_name": cust_name,
            "period_from": stmt.period_from,
            "period_to": stmt.period_to,
            "page_count": stmt.page_count,
            "rows_parsed": result.get("rows_parsed", 0),
            "failed_rows_count": result.get("failed_rows_count", 0),
            "confidence": result.get("file_confidence", 0.0),
            "review_queue_count": result.get("review_queue_count", 0),
            "opening_balance": stmt.opening_balance,
            "closing_balance": stmt.closing_balance,
            "expected_closing_balance": stmt.expected_closing_balance,
            "reconciliation_diff": stmt.reconciliation_diff,
            "reconciliation_status": stmt.reconciliation_status,
            "total_credits": stmt.total_credits,
            "total_debits": stmt.total_debits,
            "version_no": result.get("version_no", 1),
            "message": "Statement unlocked and analyzed successfully!"
        }
    except InvalidPasswordException:
        raise HTTPException(status_code=400, detail="Incorrect PDF password. Please enter the correct password and try again.")
    except PasswordRequiredException:
        raise HTTPException(status_code=400, detail="This file is password protected. Please provide the PDF password.")
    except (CorruptedPdfException, UnsupportedEncryptionException) as file_err:
        raise HTTPException(status_code=400, detail=file_err.message)
    except (NoTransactionsFoundException, OcrExtractionFailedException) as parse_err:
        raise HTTPException(status_code=422, detail=parse_err.message)
    except Exception as e:
        logger.error(f"Error unlocking statement {statement_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process statement: {str(e)}")


