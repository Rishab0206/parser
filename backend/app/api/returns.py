from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser
from app.models.models import ReturnRecord, Transaction, EmiAttempt, EmiRecord
from app.schemas.schemas import ReturnRecordResponse

router = APIRouter(prefix="/api/applications", tags=["Returns"])

@router.get("/{application_id}/returns", response_model=List[ReturnRecordResponse])
def get_application_returns(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    returns = db.query(ReturnRecord).filter(ReturnRecord.application_id == application_id).all()
    results = []

    for r in returns:
        ret_txn = db.query(Transaction).filter(Transaction.id == r.return_txn_id).first()
        orig_txn = db.query(Transaction).filter(Transaction.id == r.original_txn_id).first() if r.original_txn_id else None

        lender = "Lender"
        if r.emi_attempt_id:
            att = db.query(EmiAttempt).filter(EmiAttempt.id == r.emi_attempt_id).first()
            if att:
                rec = db.query(EmiRecord).filter(EmiRecord.id == att.emi_record_id).first()
                if rec:
                    lender = rec.lender_name

        results.append(ReturnRecordResponse(
            id=r.id,
            original_emi_date=orig_txn.txn_date if orig_txn else None,
            lender_name=lender,
            emi_amount=float(r.return_amount),
            return_date=r.return_date,
            return_amount=float(r.return_amount),
            return_charge_amount=float(r.return_charge_amount),
            charge_txn_id=r.charge_txn_id,
            reason=r.reason,
            recovery_status=r.recovery_status,
            recovery_txn_id=r.recovery_txn_id,
            source_page_no=ret_txn.source_page_no if ret_txn else 1,
            original_txn_narration=orig_txn.narration_raw if orig_txn else None,
            return_txn_narration=ret_txn.narration_raw if ret_txn else None,
            ref_no=ret_txn.ref_no if ret_txn else None
        ))

    return results

