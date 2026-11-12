import os
from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import engine, Base, get_db
from app.core.errors import (
    BSIException, bsi_exception_handler, http_exception_handler,
    validation_exception_handler, generic_exception_handler
)
from app.core.logging import logger
from app.models import *

from app.api.statements import router as statements_router
from app.api.accounts import router as accounts_router
from app.api.transactions import router as transactions_router
from app.api.emi import router as emi_router
from app.api.returns import router as returns_router
from app.api.abb import router as abb_router
from app.api.turnover import router as turnover_router
from app.api.review import router as review_router
from app.api.underwriting import router as underwriting_router

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PARSER_VERSION,
    description="Production Bank Statement Intelligence Module for Business Loan Underwriting"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(BSIException, bsi_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API Routers
app.include_router(statements_router)
app.include_router(accounts_router)
app.include_router(transactions_router)
app.include_router(emi_router)
app.include_router(returns_router)
app.include_router(abb_router)
app.include_router(turnover_router)
app.include_router(review_router)
app.include_router(underwriting_router)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.PARSER_VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/api/applications", tags=["Applications"])
def list_applications(db: Session = Depends(get_db)):
    apps = db.query(LoanApplication).order_by(LoanApplication.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "customer_id": a.customer_id,
            "customer_name": a.customer.name if a.customer else "Applicant",
            "phone_masked": a.customer.phone_masked if a.customer else "—",
            "status": a.status,
            "statement_count": len(a.statements),
            "created_at": a.created_at
        } for a in apps
    ]

@app.get("/api/customer-history", tags=["Applications"])
def get_customer_banking_history(db: Session = Depends(get_db)):
    from app.models.models import MonthlySummary, ReturnRecord, EmiRecord, Transaction, Statement
    from sqlalchemy import func

    apps = db.query(LoanApplication).order_by(LoanApplication.created_at.desc()).all()
    history = []

    for a in apps:
        stmts = a.statements
        c_name = a.customer.name if a.customer else "Applicant"
        banks = list(dict.fromkeys([s.bank_name for s in stmts if s.bank_name]))
        accs = list(dict.fromkeys([s.account_no_masked for s in stmts if s.account_no_masked]))

        min_date = db.query(func.min(Transaction.txn_date)).filter(Transaction.application_id == a.id).scalar()
        max_date = db.query(func.max(Transaction.txn_date)).filter(Transaction.application_id == a.id).scalar()
        if min_date and max_date:
            period_str = f"{min_date.strftime('%d %b')} - {max_date.strftime('%d %b %Y')}"
        else:
            period_str = "—"

        sums = db.query(MonthlySummary).filter(MonthlySummary.application_id == a.id).all()
        turnover = sum(float(m.business_turnover) for m in sums)
        abb = (sum(float(m.abb) for m in sums) / len(sums)) if sums else 0.0

        emis = db.query(EmiRecord).filter(EmiRecord.application_id == a.id).all()
        active_emis = [e for e in emis if e.status == 'ACTIVE']
        emi_monthly = sum(float(e.amount) for e in active_emis) if active_emis else (float(sums[-1].emi_burden) if sums else 0.0)

        emi_bounces = sum(m.emi_bounce_count for m in sums)
        ach_returns = db.query(ReturnRecord).filter(ReturnRecord.application_id == a.id).count()

        stmt_status = stmts[0].status if stmts else a.status

        history.append({
            "application_id": a.id,
            "customer_id": a.customer_id,
            "customer_name": c_name,
            "bank_name": ", ".join(banks) if banks else "—",
            "account_no_masked": ", ".join(accs) if accs else "—",
            "period": period_str,
            "turnover": round(turnover, 2),
            "avg_abb": round(abb, 2),
            "emi_monthly": round(emi_monthly, 2),
            "active_emi_count": len(active_emis),
            "emi_bounce": emi_bounces,
            "ach_ecs_return": ach_returns,
            "statement_count": len(stmts),
            "status": stmt_status,
            "created_at": a.created_at.strftime("%d %b %Y") if a.created_at else "—"
        })

    return history

@app.post("/api/applications/reset", tags=["Applications"])
def reset_new_application(db: Session = Depends(get_db)):
    """Creates a fresh customer application session for reset/new customer."""
    cust = Customer(name="New Applicant", phone_masked="—")
    db.add(cust)
    db.flush()
    app_obj = LoanApplication(customer_id=cust.id, status="NEW")
    db.add(app_obj)
    db.commit()
    db.refresh(app_obj)
    return {
        "id": app_obj.id,
        "customer_id": cust.id,
        "customer_name": cust.name,
        "status": app_obj.status
    }

@app.post("/api/applications", tags=["Applications"])
def create_application(name: str = "Applicant", phone: str = "9876543210", db: Session = Depends(get_db)):
    from app.core.encryption import mask_phone_number
    cust = Customer(name=name, phone_masked=mask_phone_number(phone))
    db.add(cust)
    db.flush()
    app_obj = LoanApplication(customer_id=cust.id, status="ACTIVE")
    db.add(app_obj)
    db.commit()
    db.refresh(app_obj)
    return {
        "id": app_obj.id,
        "customer_id": cust.id,
        "customer_name": cust.name,
        "phone_masked": cust.phone_masked,
        "status": app_obj.status
    }

@app.get("/api/banks/supported", tags=["Bank Coverage"])
def get_supported_banks():
    """
    Returns verified per-bank support matrix.
    NEVER claims all banks supported.
    """
    return [
        {"name": "Kotak Mahindra Bank", "code": "KOTAK", "phase": 1, "status": "Verified"},
        {"name": "HDFC Bank", "code": "HDFC", "phase": 1, "status": "Verified"},
        {"name": "ICICI Bank", "code": "ICICI", "phase": 1, "status": "Verified"},
        {"name": "State Bank of India", "code": "SBI", "phase": 1, "status": "Verified"},
        {"name": "Axis Bank", "code": "AXIS", "phase": 1, "status": "Verified"},
        {"name": "YES Bank", "code": "YES", "phase": 1, "status": "Verified"},
        {"name": "Federal Bank", "code": "FEDERAL", "phase": 1, "status": "Verified"},
        {"name": "Punjab National Bank", "code": "PNB", "phase": 2, "status": "In Validation"},
        {"name": "Bank of Baroda", "code": "BOB", "phase": 2, "status": "In Validation"},
        {"name": "Canara Bank", "code": "CANARA", "phase": 2, "status": "In Validation"},
        {"name": "Union Bank of India", "code": "UBI", "phase": 2, "status": "In Validation"},
        {"name": "IndusInd Bank", "code": "INDUS", "phase": 2, "status": "In Validation"},
        {"name": "IDFC FIRST Bank", "code": "IDFC", "phase": 2, "status": "In Validation"},
        {"name": "AU Small Finance Bank", "code": "AU", "phase": 2, "status": "In Validation"},
        {"name": "Saraswat Co-operative Bank", "code": "SARASWAT", "phase": 2, "status": "In Validation"},
        {"name": "SVC Co-operative Bank", "code": "SVC", "phase": 2, "status": "In Validation"}
    ]

