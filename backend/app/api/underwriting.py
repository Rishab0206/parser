import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_roles, CurrentUser, Role, verify_application_access
from app.models.models import (
    LoanApplication, AnalysisVersion, Statement, MonthlySummary,
    Transaction, ReturnRecord, EmiRecord, UnderwritingExport, AuditLog
)
from app.schemas.schemas import UnderwritingExportResponse, AnalysisVersionResponse

router = APIRouter(prefix="/api", tags=["Underwriting & History"])

@router.post("/underwriting/export", response_model=UnderwritingExportResponse)
def export_to_underwriting_engine(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    app_id = payload.get("application_id")
    if not app_id:
        raise HTTPException(status_code=400, detail="application_id is required")

    app_obj = verify_application_access(app_id, current_user, db)

    current_ver = db.query(AnalysisVersion).filter(
        AnalysisVersion.application_id == app_id,
        AnalysisVersion.is_current == True
    ).first()

    ver_id = current_ver.id if current_ver else "v1"

    # Gather verified metrics and source links
    monthly_rows = db.query(MonthlySummary).filter(MonthlySummary.application_id == app_id).all()
    all_txns = db.query(Transaction).filter(Transaction.application_id == app_id).all()
    all_stmts = db.query(Statement).filter(Statement.application_id == app_id).all()
    returns = db.query(ReturnRecord).filter(ReturnRecord.application_id == app_id).all()
    emis = db.query(EmiRecord).filter(EmiRecord.application_id == app_id).all()

    total_turnover = sum(float(m.business_turnover) for m in monthly_rows)
    avg_turnover = (total_turnover / len(monthly_rows)) if monthly_rows else 0.0

    export_payload = {
        "application_id": app_id,
        "analysis_version_id": ver_id,
        "exported_at": datetime.datetime.utcnow().isoformat(),
        "bank_analysis": {
            "months_analysed": len(monthly_rows),
            "avg_monthly_turnover": round(avg_turnover, 2),
            "monthly_turnover": [
                {"month": m.month, "turnover": float(m.business_turnover)} for m in monthly_rows
            ],
            "abb_by_month": [
                {"month": m.month, "abb": float(m.abb)} for m in monthly_rows
            ],
            "min_balance": min([float(m.min_balance) for m in monthly_rows]) if monthly_rows else 0.0,
            "negative_days": sum(m.negative_days for m in monthly_rows),
            "emi_burden_monthly": [
                {"month": m.month, "emi_burden": float(m.emi_burden)} for m in monthly_rows
            ],
            "emi_bounce_count": sum(m.emi_bounce_count for m in monthly_rows),
            "return_counts": len(returns),
            "internal_transfers_excluded": sum(float(m.internal_transfer_credit_excluded) for m in monthly_rows),
            "confidence_scores": {
                "file_confidence": current_ver.summary_json.get("file_confidence", 85.0) if current_ver else 85.0
            }
        },
        "source_links": [
            {
                "metric": "business_turnover",
                "transaction_ids": [t.id for t in all_txns if t.category == "BUSINESS_RECEIPT"],
                "statement_ids": [s.id for s in all_stmts],
                "page_nos": list(set(t.source_page_no for t in all_txns if t.category == "BUSINESS_RECEIPT"))
            },
            {
                "metric": "returns",
                "transaction_ids": [r.return_txn_id for r in returns],
                "statement_ids": [s.id for s in all_stmts],
                "page_nos": list(set(r.return_record_page for r in returns if hasattr(r, "return_record_page")))
            }
        ]
    }

    # Save export record
    exp = UnderwritingExport(
        application_id=app_id,
        analysis_version_id=ver_id,
        payload_json=export_payload,
        status="EXPORTED"
    )
    db.add(exp)

    audit = AuditLog(
        user_id=current_user.user_id,
        action="UNDERWRITING_EXPORT",
        entity="LoanApplication",
        entity_id=app_id,
        old_value=None,
        new_value={"export_id": exp.id, "version_id": ver_id}
    )
    db.add(audit)
    db.commit()
    db.refresh(exp)

    return UnderwritingExportResponse(
        export_id=exp.id,
        application_id=exp.application_id,
        analysis_version_id=exp.analysis_version_id,
        payload=exp.payload_json,
        status=exp.status,
        sent_to_engine_at=exp.sent_to_engine_at
    )

@router.get("/applications/{application_id}/history", response_model=List[AnalysisVersionResponse])
def get_analysis_history(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    verify_application_access(application_id, current_user, db)
    versions = db.query(AnalysisVersion).filter(
        AnalysisVersion.application_id == application_id
    ).order_by(AnalysisVersion.version_no.desc()).all()

    return [
        AnalysisVersionResponse(
            id=v.id,
            version_no=v.version_no,
            created_by=v.created_by,
            created_at=v.created_at,
            is_current=v.is_current,
            summary=v.summary_json
        ) for v in versions
    ]

