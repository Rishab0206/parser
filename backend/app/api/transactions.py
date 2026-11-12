from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser
from app.models.models import Transaction, Statement
from app.schemas.schemas import TransactionListResponse, TransactionResponse

router = APIRouter(prefix="/api/applications", tags=["Transactions"])

@router.get("/{application_id}/transactions", response_model=TransactionListResponse)
def get_application_transactions(
    application_id: str,
    search: Optional[str] = Query(None),
    bank: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    account_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    query = db.query(Transaction, Statement).join(
        Statement, Transaction.statement_id == Statement.id
    ).filter(Transaction.application_id == application_id)

    if account_id:
        query = query.filter(Transaction.statement_id == account_id)

    if bank:
        query = query.filter(Statement.bank_name.ilike(f"%{bank}%"))

    if month:
        query = query.filter(Transaction.txn_date.startswith(month))

    if channel and channel != "ALL":
        query = query.filter(Transaction.channel == channel)

    if category and category != "ALL":
        query = query.filter(Transaction.category == category)

    if search:
        search_filter = or_(
            Transaction.narration_raw.ilike(f"%{search}%"),
            Transaction.ref_no.ilike(f"%{search}%"),
            Transaction.counterparty.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)

    total = query.count()
    offset = (page - 1) * page_size
    records = query.order_by(Transaction.txn_date.desc(), Transaction.id.desc()).offset(offset).limit(page_size).all()

    items = []
    for txn, stmt in records:
        t_resp = TransactionResponse(
            id=txn.id,
            statement_id=txn.statement_id,
            txn_date=txn.txn_date,
            value_date=txn.value_date,
            narration_raw=txn.narration_raw,
            narration_clean=txn.narration_clean,
            ref_no=txn.ref_no,
            utr=txn.utr,
            debit=float(txn.debit),
            credit=float(txn.credit),
            balance=float(txn.balance),
            channel=txn.channel,
            counterparty=txn.counterparty,
            category=txn.category,
            confidence=float(txn.confidence),
            source_page_no=txn.source_page_no,
            is_duplicate=txn.is_duplicate,
            is_internal_transfer=txn.is_internal_transfer,
            internal_match_id=txn.internal_match_id,
            statement_bank=stmt.bank_name,
            statement_account_masked=stmt.account_no_masked
        )
        items.append(t_resp)

    return TransactionListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )

