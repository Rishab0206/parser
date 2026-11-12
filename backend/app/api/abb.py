from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser, verify_application_access
from app.models.models import MonthlySummary
from app.schemas.schemas import MonthlySummaryResponse

router = APIRouter(prefix="/api/applications", tags=["ABB"])

@router.get("/{application_id}/abb", response_model=List[MonthlySummaryResponse])
def get_application_abb(
    application_id: str,
    account_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    verify_application_access(application_id, current_user, db)
    query = db.query(MonthlySummary).filter(MonthlySummary.application_id == application_id)
    if account_id:
        query = query.filter(MonthlySummary.account_id == account_id)

    summaries = query.order_by(MonthlySummary.month.asc()).all()

    results = []
    for s in summaries:
        b_turnover = float(s.business_turnover)
        burden = float(s.emi_burden)
        ratio = (burden / b_turnover * 100.0) if b_turnover > 0 else 0.0

        results.append(MonthlySummaryResponse(
            month=s.month,
            gross_credit=float(s.gross_credit),
            business_turnover=b_turnover,
            non_business_credit=float(s.non_business_credit),
            internal_transfer_credit_excluded=float(s.internal_transfer_credit_excluded),
            total_debit=float(s.total_debit),
            net_flow=float(s.net_flow),
            abb=float(s.abb),
            min_balance=float(s.min_balance),
            max_balance=float(s.max_balance),
            min_balance_date=s.min_balance_date,
            month_end_balance=float(s.month_end_balance),
            negative_days=s.negative_days,
            days_below_5000=s.days_below_5000,
            days_below_10000=s.days_below_10000,
            emi_burden=burden,
            emi_bounce_count=s.emi_bounce_count,
            emi_to_turnover_ratio=round(ratio, 2)
        ))

    return results

