from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser, verify_application_access
from app.models.models import Statement, MonthlySummary, EmiRecord, Transaction
from app.schemas.schemas import AccountCardResponse

router = APIRouter(prefix="/api/applications", tags=["Accounts"])

@router.get("/{application_id}/accounts", response_model=List[AccountCardResponse])
def get_application_accounts(
    application_id: str,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    verify_application_access(application_id, current_user, db)
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

        is_parsed_ok = stmt.status in ["PARSED", "PARSED_WITH_WARNINGS", "NEEDS_REVIEW"] and len(summaries) > 0
        if is_parsed_ok:
            stmt_turnover = round(sum(float(s.business_turnover) for s in summaries), 2)
            stmt_abb = round(sum(float(s.abb) for s in summaries) / len(summaries), 2)
            total_turnover += stmt_turnover
            total_abb_sum += stmt_abb
        else:
            stmt_turnover = None
            stmt_abb = None

        if stmt.period_from:
            if not overall_period_from or stmt.period_from < overall_period_from:
                overall_period_from = stmt.period_from
        if stmt.period_to:
            if not overall_period_to or stmt.period_to > overall_period_to:
                overall_period_to = stmt.period_to

        account_cards.append(AccountCardResponse(
            account_id=stmt.id,
            bank_name=stmt.bank_name or "Unknown Bank",
            account_no_masked=stmt.account_no_masked or "XXXX----",
            account_type=stmt.account_type or "SAVINGS",
            ifsc=stmt.ifsc,
            period_from=stmt.period_from,
            period_to=stmt.period_to,
            abb=stmt_abb,
            turnover=stmt_turnover,
            opening_balance=stmt.opening_balance,
            closing_balance=stmt.closing_balance,
            reconciliation_status=stmt.reconciliation_status,
            reconciliation_diff=stmt.reconciliation_diff,
            emi_count=total_emi_count if is_parsed_ok else 0,
            status=stmt.status,
            error_message=stmt.error_message,
            is_consolidated=False
        ))

    # Add Consolidated Card at the beginning
    parsed_cards = [c for c in account_cards if c.abb is not None]
    if parsed_cards:
        consolidated_abb = round(total_abb_sum / len(parsed_cards), 2)
        consolidated_turnover = round(total_turnover, 2)
        has_warnings = any(c.status in ["PARSED_WITH_WARNINGS", "NEEDS_REVIEW"] for c in parsed_cards)
        consolidated_status = "PARSED_WITH_WARNINGS" if has_warnings else "PARSED"
    else:
        consolidated_abb = None
        consolidated_turnover = None
        consolidated_status = statements[-1].status if statements else "PARSING_FAILED"

    consolidated_card = AccountCardResponse(
        account_id=None,
        bank_name="All Accounts (Consolidated)",
        account_no_masked="Consolidated",
        account_type="CONSOLIDATED",
        period_from=overall_period_from,
        period_to=overall_period_to,
        abb=consolidated_abb,
        turnover=consolidated_turnover,
        emi_count=total_emi_count if parsed_cards else 0,
        status=consolidated_status,
        error_message=statements[-1].error_message if not parsed_cards and statements else None,
        is_consolidated=True
    )

    return [consolidated_card] + account_cards

