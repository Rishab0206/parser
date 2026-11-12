import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles, CurrentUser, Role, verify_application_access
from app.models.models import ReviewQueue, Transaction, AuditLog, AnalysisVersion, MonthlySummary
from app.schemas.schemas import ReviewQueueItemResponse, ReviewResolveRequest

router = APIRouter(prefix="/api", tags=["Review Queue"])

@router.get("/applications/{application_id}/review-queue", response_model=List[ReviewQueueItemResponse])
def get_application_review_queue(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    verify_application_access(application_id, current_user, db)
    items = db.query(ReviewQueue).filter(
        ReviewQueue.application_id == application_id,
        ReviewQueue.status == "OPEN"
    ).order_by(ReviewQueue.confidence.asc()).all()

    results = []
    for it in items:
        txn = None
        if it.transaction_id:
            txn = db.query(Transaction).filter(Transaction.id == it.transaction_id).first()

        results.append(ReviewQueueItemResponse(
            id=it.id,
            statement_id=it.statement_id,
            transaction_id=it.transaction_id,
            issue_type=it.issue_type,
            confidence=it.confidence,
            suggested_value=it.suggested_value,
            status=it.status,
            narration_raw=txn.narration_raw if txn else (it.suggested_value.get("narration") if it.suggested_value else None),
            source_page_no=txn.source_page_no if txn else 1,
            amount=float(txn.debit or txn.credit) if txn else None,
            date=txn.txn_date if txn else None,
            created_at=it.created_at
        ))

    return results

@router.post("/review/{review_id}/resolve")
def resolve_review_item(
    review_id: str,
    request: ReviewResolveRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_roles([Role.ADMIN, Role.UNDERWRITER]))
):
    review_item = db.query(ReviewQueue).filter(ReviewQueue.id == review_id).first()
    if not review_item:
        raise HTTPException(status_code=404, detail="Review item not found")

    old_status = review_item.status
    review_item.status = request.action  # APPROVED or REJECTED
    review_item.resolution_notes = request.reason
    review_item.resolved_by = current_user.username
    review_item.resolved_at = datetime.datetime.utcnow()

    # If action is CORRECT or APPROVE with corrected values, update target transaction
    if request.corrected_value and review_item.transaction_id:
        txn = db.query(Transaction).filter(Transaction.id == review_item.transaction_id).first()
        if txn:
            old_val = {"debit": float(txn.debit), "credit": float(txn.credit), "balance": float(txn.balance)}
            if "debit" in request.corrected_value:
                txn.debit = request.corrected_value["debit"]
            if "credit" in request.corrected_value:
                txn.credit = request.corrected_value["credit"]
            if "balance" in request.corrected_value:
                txn.balance = request.corrected_value["balance"]
            if "category" in request.corrected_value:
                txn.category = request.corrected_value["category"]

            # Log audit
            audit = AuditLog(
                user_id=current_user.user_id,
                action="MANUAL_CORRECTION",
                entity="Transaction",
                entity_id=txn.id,
                old_value=old_val,
                new_value=request.corrected_value
            )
            db.add(audit)

    # Version recalculation: create new analysis version (PART 3)
    current_version_count = db.query(AnalysisVersion).filter(
        AnalysisVersion.application_id == review_item.application_id
    ).count()
    new_version_no = current_version_count + 1

    db.query(AnalysisVersion).filter(
        AnalysisVersion.application_id == review_item.application_id
    ).update({"is_current": False})

    new_ver = AnalysisVersion(
        application_id=review_item.application_id,
        version_no=new_version_no,
        summary_json={
            "version_no": new_version_no,
            "resolved_review_id": review_item.id,
            "action": request.action,
            "reason": request.reason
        },
        created_by=current_user.username,
        is_current=True
    )
    db.add(new_ver)
    db.commit()

    return {
        "status": "RESOLVED",
        "review_id": review_item.id,
        "new_version_no": new_version_no
    }

