from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser
from app.models.models import MonthlySummary, Statement, ReviewQueue, ReturnRecord, EmiRecord
from app.schemas.schemas import SummaryKpiResponse, MonthlySummaryResponse

router = APIRouter(prefix="/api/applications", tags=["Turnover & Summary"])

@router.get("/{application_id}/summary", response_model=SummaryKpiResponse)
def get_application_summary(
    application_id: str,
    account_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    stmt_count = db.query(Statement).filter(Statement.application_id == application_id).count()
    if stmt_count == 0:
        return SummaryKpiResponse(
            total_business_turnover=0.0,
            avg_monthly_turnover=0.0,
            total_debit=0.0,
            net_cash_flow=0.0,
            avg_monthly_abb=0.0,
            emi_bounce_count=0,
            total_ecs_returns=0,
            emi_to_turnover_ratio=0.0,
            total_negative_days=0,
            review_queue_count=0,
            internal_transfers_excluded=0.0,
            monthly_breakdown=[],
            has_data=False
        )

    query = db.query(MonthlySummary).filter(MonthlySummary.application_id == application_id)
    if account_id:
        query = query.filter(MonthlySummary.account_id == account_id)

    monthly_rows = query.order_by(MonthlySummary.month.asc()).all()

    total_turnover = sum(float(m.business_turnover) for m in monthly_rows)
    total_debit = sum(float(m.total_debit) for m in monthly_rows)
    net_cash_flow = round(total_turnover - total_debit, 2)
    avg_turnover = (total_turnover / len(monthly_rows)) if monthly_rows else 0.0
    avg_abb = (sum(float(m.abb) for m in monthly_rows) / len(monthly_rows)) if monthly_rows else 0.0

    total_bounces = sum(m.emi_bounce_count for m in monthly_rows)
    total_negative_days = sum(m.negative_days for m in monthly_rows)
    internal_excluded = sum(float(m.internal_transfer_credit_excluded) for m in monthly_rows)

    total_returns = db.query(ReturnRecord).filter(ReturnRecord.application_id == application_id).count()
    rq_count = db.query(ReviewQueue).filter(
        ReviewQueue.application_id == application_id,
        ReviewQueue.status == "OPEN"
    ).count()

    # Overall EMI-to-Turnover ratio
    total_emi_burden = sum(float(m.emi_burden) for m in monthly_rows)
    overall_ratio = (total_emi_burden / total_turnover * 100.0) if total_turnover > 0 else 0.0

    breakdown = []
    for s in monthly_rows:
        b_turnover = float(s.business_turnover)
        burden = float(s.emi_burden)
        ratio = (burden / b_turnover * 100.0) if b_turnover > 0 else 0.0

        breakdown.append(MonthlySummaryResponse(
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

    return SummaryKpiResponse(
        total_business_turnover=round(total_turnover, 2),
        avg_monthly_turnover=round(avg_turnover, 2),
        total_debit=round(total_debit, 2),
        net_cash_flow=net_cash_flow,
        avg_monthly_abb=round(avg_abb, 2),
        emi_bounce_count=total_bounces,
        total_ecs_returns=total_returns,
        emi_to_turnover_ratio=round(overall_ratio, 2),
        total_negative_days=total_negative_days,
        review_queue_count=rq_count,
        internal_transfers_excluded=round(internal_excluded, 2),
        monthly_breakdown=breakdown,
        has_data=True
    )

