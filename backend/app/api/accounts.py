from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser
from app.models.models import Statement, MonthlySummary, EmiRecord, Transaction
from app.schemas.schemas import AccountCardResponse

router = APIRouter(prefix="/api/applications", tags=["Accounts"])

@router.get("/{application_id}/accounts", response_model=List[AccountCardResponse])
def get_application_accounts(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    statements = db.query(Statement).filter(Statement.application_id == application_id).all()
    if not statements:
        return []

    account_cards = []
    total_turnover = 0.0
    total_abb_sum = 0.0
    total_emi_count = db.query(EmiRecord).filter(EmiRecord.application_id == application_id).count()

    overall_period_from = None
    overall_period_to = None

    for stmt in statements:
        # Compute monthly metrics for this statement
        summaries = db.query(MonthlySummary).filter(
            MonthlySummary.application_id == application_id,
            MonthlySummary.account_id == stmt.id
        ).all()

        stmt_turnover = sum(float(s.business_turnover) for s in summaries)
        stmt_abb = (sum(float(s.abb) for s in summaries) / len(summaries)) if summaries else 0.0

        if stmt.period_from:
            if not overall_period_from or stmt.period_from < overall_period_from:
                overall_period_from = stmt.period_from
        if stmt.period_to:
            if not overall_period_to or stmt.period_to > overall_period_to:
                overall_period_to = stmt.period_to

        total_turnover += stmt_turnover
        total_abb_sum += stmt_abb

        account_cards.append(AccountCardResponse(
            account_id=stmt.id,
            bank_name=stmt.bank_name or "Unknown Bank",
            account_no_masked=stmt.account_no_masked or "XXXX----",
            account_type=stmt.account_type or "SAVINGS",
            period_from=stmt.period_from,
            period_to=stmt.period_to,
            abb=round(stmt_abb, 2),
            turnover=round(stmt_turnover, 2),
            emi_count=total_emi_count,
            status=stmt.status,
            is_consolidated=False
        ))

    # Add Consolidated Card at the beginning
    consolidated_abb = (total_abb_sum / len(statements)) if statements else 0.0
    consolidated_card = AccountCardResponse(
        account_id=None,
        bank_name="All Accounts (Consolidated)",
        account_no_masked="Consolidated",
        account_type="CONSOLIDATED",
        period_from=overall_period_from,
        period_to=overall_period_to,
        abb=round(consolidated_abb, 2),
        turnover=round(total_turnover, 2),
        emi_count=total_emi_count,
        status="PARSED",
        is_consolidated=True
    )

    return [consolidated_card] + account_cards

