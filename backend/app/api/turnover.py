from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser, verify_application_access
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
    verify_application_access(application_id, current_user, db)
    statements = db.query(Statement).filter(Statement.application_id == application_id).all()
    if not statements:
        return SummaryKpiResponse(
            monthly_breakdown=[],
            has_data=False
        )

    query = db.query(MonthlySummary).filter(MonthlySummary.application_id == application_id)
    if account_id:
        query = query.filter(MonthlySummary.account_id == account_id)

    monthly_rows = query.order_by(MonthlySummary.month.asc()).all()

    target_stmts = [s for s in statements if not account_id or s.id == account_id]
    latest_stmt = target_stmts[-1] if target_stmts else statements[-1]

    # Never convert failed/unparsed statements into misleading zero values
    if not monthly_rows:
        return SummaryKpiResponse(
            review_queue_count=db.query(ReviewQueue).filter(
                ReviewQueue.application_id == application_id,
                ReviewQueue.status == "OPEN"
            ).count(),
            parsing_status=latest_stmt.status,
            error_message=latest_stmt.error_message,
            reconciliation_status=latest_stmt.reconciliation_status or "UNAVAILABLE",
            monthly_breakdown=[],
            has_data=False
        )

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

    from app.models.models import Transaction
    txn_query = db.query(Transaction).filter(Transaction.application_id == application_id)
    if account_id:
        txn_query = txn_query.filter(Transaction.statement_id == account_id)
    total_txns = txn_query.count()

    parsed_stmts = [s for s in target_stmts if s.status in ["PARSED", "PARSED_WITH_WARNINGS", "NEEDS_REVIEW"]]
    opening_bal = None
    closing_bal = None
    total_creds = round(sum(float(m.gross_credit) for m in monthly_rows), 2)
    recon_status = None
    recon_diff = None

    if parsed_stmts:
        if len(parsed_stmts) == 1:
            opening_bal = parsed_stmts[0].opening_balance
            closing_bal = parsed_stmts[0].closing_balance
            recon_status = parsed_stmts[0].reconciliation_status
            recon_diff = parsed_stmts[0].reconciliation_diff
        else:
            vals_open = [s.opening_balance for s in parsed_stmts if s.opening_balance is not None]
            vals_close = [s.closing_balance for s in parsed_stmts if s.closing_balance is not None]
            opening_bal = round(sum(vals_open), 2) if vals_open else None
            closing_bal = round(sum(vals_close), 2) if vals_close else None
            any_mismatch = any(s.reconciliation_status == "MISMATCH" for s in parsed_stmts)
            recon_status = "MISMATCH" if any_mismatch else "MATCHED"

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
        opening_balance=opening_bal,
        closing_balance=closing_bal,
        total_credits=total_creds,
        total_transactions=total_txns,
        reconciliation_status=recon_status,
        reconciliation_diff=recon_diff,
        parsing_status=latest_stmt.status,
        error_message=latest_stmt.error_message,
        monthly_breakdown=breakdown,
        has_data=True
    )

