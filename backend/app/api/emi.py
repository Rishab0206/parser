from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser
from app.models.models import EmiRecord, EmiAttempt, Transaction, Statement
from app.schemas.schemas import EmiRecordResponse, EmiDetailResponse, EmiAttemptResponse

router = APIRouter(prefix="/api/applications", tags=["EMI Intelligence"])

@router.get("/{application_id}/emi", response_model=List[EmiRecordResponse])
def get_application_emis(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    emis = db.query(EmiRecord).filter(EmiRecord.application_id == application_id).all()
    results = []

    for e in emis:
        # Get latest attempt
        latest_att = db.query(EmiAttempt).filter(
            EmiAttempt.emi_record_id == e.id
        ).order_by(EmiAttempt.attempt_date.desc()).first()

        stmt_info = None
        if latest_att:
            txn = db.query(Transaction).filter(Transaction.id == latest_att.transaction_id).first()
            if txn:
                stmt_info = db.query(Statement).filter(Statement.id == txn.statement_id).first()

        results.append(EmiRecordResponse(
            id=e.id,
            lender_name=e.lender_name,
            lender_confidence=e.lender_confidence,
            mandate_ref=e.mandate_ref,
            amount=float(e.amount),
            frequency=e.frequency,
            first_date=e.first_date,
            last_date=e.last_date,
            total_attempts=e.total_attempts,
            total_success=e.total_success,
            total_returns=e.total_returns,
            status=e.status,
            latest_mode="NACH",
            latest_date=latest_att.attempt_date if latest_att else e.last_date,
            masked_account=stmt_info.account_no_masked if stmt_info else "XXXX----",
            bank_name=stmt_info.bank_name if stmt_info else "Bank"
        ))

    return results

@router.get("/{application_id}/emi/{emi_id}", response_model=EmiDetailResponse)
def get_emi_detail(
    application_id: str,
    emi_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    emi = db.query(EmiRecord).filter(
        EmiRecord.id == emi_id,
        EmiRecord.application_id == application_id
    ).first()
    if not emi:
        raise HTTPException(status_code=404, detail="EMI record not found")

    attempts_db = db.query(EmiAttempt, Transaction).join(
        Transaction, EmiAttempt.transaction_id == Transaction.id
    ).filter(EmiAttempt.emi_record_id == emi.id).order_by(EmiAttempt.attempt_date.desc()).all()

    attempts = []
    for att, txn in attempts_db:
        attempts.append(EmiAttemptResponse(
            id=att.id,
            attempt_date=att.attempt_date,
            amount=float(att.amount),
            status=att.status,
            return_id=att.return_id,
            transaction_id=att.transaction_id,
            narration_raw=txn.narration_raw,
            source_page_no=txn.source_page_no,
            ref_no=txn.ref_no
        ))

    total_att = len(attempts)
    bounce_count = sum(1 for a in attempts if a.status == "RETURNED")
    bounce_rate = (bounce_count / total_att * 100.0) if total_att > 0 else 0.0

    last_3 = attempts[:3]

    # Recovery info if any return was recovered
    from app.models.models import ReturnRecord
    returns = db.query(ReturnRecord).filter(
        ReturnRecord.emi_attempt_id.in_([a.id for a in attempts])
    ).all()
    recovery_info = None
    if returns:
        recovered = sum(1 for r in returns if r.recovery_status == "RECOVERED")
        recovery_info = {
            "total_returns": len(returns),
            "recovered_count": recovered,
            "recovery_rate_pct": round(recovered / len(returns) * 100.0, 1)
        }

    return EmiDetailResponse(
        emi_record=EmiRecordResponse(
            id=emi.id,
            lender_name=emi.lender_name,
            lender_confidence=emi.lender_confidence,
            mandate_ref=emi.mandate_ref,
            amount=float(emi.amount),
            frequency=emi.frequency,
            first_date=emi.first_date,
            last_date=emi.last_date,
            total_attempts=emi.total_attempts,
            total_success=emi.total_success,
            total_returns=emi.total_returns,
            status=emi.status,
            latest_mode="NACH",
            latest_date=attempts[0].attempt_date if attempts else emi.last_date,
            masked_account="XXXX----",
            bank_name="Bank"
        ),
        attempts=attempts,
        bounce_rate=round(bounce_rate, 2),
        last_3_attempts=last_3,
        recovery_info=recovery_info
    )

