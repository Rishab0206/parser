import datetime
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date, ForeignKey, Text, JSON, Numeric
)
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), default="Staff")  # "Admin" or "Staff"
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    applications = relationship("LoanApplication", back_populates="owner")
    invites_created = relationship("Invite", back_populates="creator")

class Invite(Base):
    __tablename__ = "invites"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    token = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(32), default="Staff")
    created_by_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    creator = relationship("User", back_populates="invites_created")

class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    phone_masked = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    applications = relationship("LoanApplication", back_populates="customer", cascade="all, delete-orphan")

class LoanApplication(Base):
    __tablename__ = "loan_applications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False)
    owner_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="applications")
    customer = relationship("Customer", back_populates="applications")
    statements = relationship("Statement", back_populates="application", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="application", cascade="all, delete-orphan")
    emi_records = relationship("EmiRecord", back_populates="application", cascade="all, delete-orphan")
    return_records = relationship("ReturnRecord", back_populates="application", cascade="all, delete-orphan")
    monthly_summaries = relationship("MonthlySummary", back_populates="application", cascade="all, delete-orphan")
    versions = relationship("AnalysisVersion", back_populates="application", cascade="all, delete-orphan")
    review_items = relationship("ReviewQueue", back_populates="application", cascade="all, delete-orphan")
    underwriting_exports = relationship("UnderwritingExport", back_populates="application", cascade="all, delete-orphan")

class Statement(Base):
    __tablename__ = "statements"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("loan_applications.id"), nullable=False)
    owner_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    file_name_original = Column(String(255), nullable=False)
    file_hash_sha256 = Column(String(64), nullable=False, index=True)
    file_path_encrypted = Column(String(512), nullable=False)
    bank_name = Column(String(100), nullable=True)
    bank_detect_confidence = Column(Float, default=0.0)
    account_no_masked = Column(String(32), nullable=True)
    account_no_encrypted = Column(Text, nullable=True)
    account_type = Column(String(20), default="SAVINGS")  # SAVINGS / CURRENT / OD / CC
    ifsc = Column(String(20), nullable=True)
    branch = Column(String(100), nullable=True)
    period_from = Column(Date, nullable=True)
    period_to = Column(Date, nullable=True)
    page_count = Column(Integer, default=1)
    parser_version = Column(String(20), default="2.0.0")
    status = Column(String(30), default="FILE_UPLOADED")  # FILE_UPLOADED, PASSWORD_REQUIRED, PASSWORD_VERIFIED, PARSING, PARSED, PARSED_WITH_WARNINGS, PARSING_FAILED, INVALID_FILE
    error_message = Column(Text, nullable=True)
    opening_balance = Column(Float, nullable=True)
    closing_balance = Column(Float, nullable=True)
    expected_closing_balance = Column(Float, nullable=True)
    reconciliation_diff = Column(Float, nullable=True)
    reconciliation_status = Column(String(30), nullable=True)  # MATCHED, MISMATCH, UNAVAILABLE
    total_credits = Column(Float, nullable=True)
    total_debits = Column(Float, nullable=True)
    uploaded_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    application = relationship("LoanApplication", back_populates="statements")
    transactions = relationship("Transaction", back_populates="statement", cascade="all, delete-orphan")
    review_items = relationship("ReviewQueue", back_populates="statement", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    statement_id = Column(String(36), ForeignKey("statements.id"), nullable=False)
    application_id = Column(String(36), ForeignKey("loan_applications.id"), nullable=False)
    txn_date = Column(Date, nullable=False, index=True)
    value_date = Column(Date, nullable=True)
    narration_raw = Column(Text, nullable=False)
    narration_clean = Column(Text, nullable=True)
    ref_no = Column(String(128), nullable=True)
    utr = Column(String(128), nullable=True)
    debit = Column(Numeric(14, 2), default=0.0)
    credit = Column(Numeric(14, 2), default=0.0)
    balance = Column(Numeric(14, 2), nullable=False)
    channel = Column(String(32), default="OTHER")
    counterparty = Column(String(255), nullable=True)
    category = Column(String(64), default="UNCATEGORIZED")
    confidence = Column(Float, default=100.0)
    source_page_no = Column(Integer, nullable=False, default=1)
    row_hash = Column(String(64), nullable=False, index=True)
    is_duplicate = Column(Boolean, default=False)
    is_internal_transfer = Column(Boolean, default=False)
    internal_match_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    statement = relationship("Statement", back_populates="transactions")
    application = relationship("LoanApplication", back_populates="transactions")
    emi_attempts = relationship("EmiAttempt", back_populates="transaction")

class EmiRecord(Base):
    __tablename__ = "emi_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("loan_applications.id"), nullable=False)
    lender_name = Column(String(255), nullable=False)
    lender_confidence = Column(String(32), default="CONFIRMED")  # CONFIRMED, PROBABLE, POSSIBLE
    mandate_ref = Column(String(128), nullable=True)
    amount = Column(Numeric(14, 2), nullable=False)
    frequency = Column(String(32), default="MONTHLY")  # MONTHLY, WEEKLY, QUARTERLY, VARIABLE
    first_date = Column(Date, nullable=True)
    last_date = Column(Date, nullable=True)
    total_attempts = Column(Integer, default=0)
    total_success = Column(Integer, default=0)
    total_returns = Column(Integer, default=0)
    status = Column(String(32), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    application = relationship("LoanApplication", back_populates="emi_records")
    attempts = relationship("EmiAttempt", back_populates="emi_record", cascade="all, delete-orphan")

class EmiAttempt(Base):
    __tablename__ = "emi_attempts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    emi_record_id = Column(String(36), ForeignKey("emi_records.id"), nullable=False)
    transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=False)
    attempt_date = Column(Date, nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    status = Column(String(32), default="SUCCESS")  # SUCCESS, RETURNED, PENDING
    return_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    emi_record = relationship("EmiRecord", back_populates="attempts")
    transaction = relationship("Transaction", back_populates="emi_attempts")
    return_records = relationship("ReturnRecord", back_populates="emi_attempt")

class ReturnRecord(Base):
    __tablename__ = "return_records"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("loan_applications.id"), nullable=False)
    emi_attempt_id = Column(String(36), ForeignKey("emi_attempts.id"), nullable=True)
    original_txn_id = Column(String(36), ForeignKey("transactions.id"), nullable=True)
    return_txn_id = Column(String(36), ForeignKey("transactions.id"), nullable=False)
    return_date = Column(Date, nullable=False)
    return_amount = Column(Numeric(14, 2), nullable=False)
    return_charge_amount = Column(Numeric(14, 2), default=0.0)
    charge_txn_id = Column(String(36), nullable=True)
    reason = Column(String(64), default="INSUFFICIENT_FUNDS")  # INSUFFICIENT_FUNDS, ACCOUNT_CLOSED, OTHER
    recovery_status = Column(String(32), default="NOT_RECOVERED")  # NOT_RECOVERED, RECOVERED, PARTIAL
    recovery_txn_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    application = relationship("LoanApplication", back_populates="return_records")
    emi_attempt = relationship("EmiAttempt", back_populates="return_records")

class MonthlySummary(Base):
    __tablename__ = "monthly_summaries"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("loan_applications.id"), nullable=False)
    account_id = Column(String(36), nullable=True)  # Nullable for consolidated summary
    month = Column(String(7), nullable=False, index=True)  # YYYY-MM
    gross_credit = Column(Numeric(14, 2), default=0.0)
    business_turnover = Column(Numeric(14, 2), default=0.0)
    non_business_credit = Column(Numeric(14, 2), default=0.0)
    internal_transfer_credit_excluded = Column(Numeric(14, 2), default=0.0)
    total_debit = Column(Numeric(14, 2), default=0.0)
    net_flow = Column(Numeric(14, 2), default=0.0)
    abb = Column(Numeric(14, 2), default=0.0)
    min_balance = Column(Numeric(14, 2), default=0.0)
    max_balance = Column(Numeric(14, 2), default=0.0)
    min_balance_date = Column(Date, nullable=True)
    month_end_balance = Column(Numeric(14, 2), default=0.0)
    negative_days = Column(Integer, default=0)
    days_below_5000 = Column(Integer, default=0)
    days_below_10000 = Column(Integer, default=0)
    emi_burden = Column(Numeric(14, 2), default=0.0)
    emi_bounce_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    application = relationship("LoanApplication", back_populates="monthly_summaries")

class AnalysisVersion(Base):
    __tablename__ = "analysis_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("loan_applications.id"), nullable=False)
    version_no = Column(Integer, nullable=False)
    summary_json = Column(JSON, nullable=False)
    created_by = Column(String(100), default="system")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_current = Column(Boolean, default=True)

    application = relationship("LoanApplication", back_populates="versions")

class ReviewQueue(Base):
    __tablename__ = "review_queue"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("loan_applications.id"), nullable=False)
    transaction_id = Column(String(36), ForeignKey("transactions.id"), nullable=True)
    statement_id = Column(String(36), ForeignKey("statements.id"), nullable=False)
    issue_type = Column(String(64), nullable=False)  # LOW_CONFIDENCE, BALANCE_MISMATCH, UNKNOWN_BANK, AMBIGUOUS_EMI, CROSS_ACCOUNT_REVIEW
    confidence = Column(Float, default=50.0)
    suggested_value = Column(JSON, nullable=True)
    status = Column(String(32), default="OPEN")  # OPEN, APPROVED, REJECTED
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    application = relationship("LoanApplication", back_populates="review_items")
    statement = relationship("Statement", back_populates="review_items")

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(100), nullable=False)
    action = Column(String(64), nullable=False)  # UPLOAD, PARSE, MANUAL_CORRECT, RESOLVE_REVIEW, EXPORT
    entity = Column(String(64), nullable=False)   # Statement, Transaction, EmiRecord, AnalysisVersion
    entity_id = Column(String(64), nullable=False)
    old_value = Column(JSON, nullable=True)
    new_value = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    ip = Column(String(45), nullable=True)

class UnderwritingExport(Base):
    __tablename__ = "underwriting_exports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    application_id = Column(String(36), ForeignKey("loan_applications.id"), nullable=False)
    analysis_version_id = Column(String(36), ForeignKey("analysis_versions.id"), nullable=False)
    payload_json = Column(JSON, nullable=False)
    sent_to_engine_at = Column(DateTime, default=datetime.datetime.utcnow)
    engine_response = Column(JSON, nullable=True)
    status = Column(String(32), default="EXPORTED")  # EXPORTED, DELIVERED, FAILED

    application = relationship("LoanApplication", back_populates="underwriting_exports")

