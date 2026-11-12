from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from decimal import Decimal

class CustomerBase(BaseModel):
    name: str
    phone_masked: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class StatementStatusResponse(BaseModel):
    statement_id: str
    status: str
    bank_name: Optional[str] = None
    bank_detect_confidence: float = 0.0
    account_no_masked: Optional[str] = None
    account_type: str = "SAVINGS"
    page_count: int = 1
    rows_parsed: int = 0
    failed_rows_count: int = 0
    confidence: float = 0.0
    review_queue_count: int = 0
    error_message: Optional[str] = None
    error_report: Optional[Dict[str, Any]] = None

class AccountCardResponse(BaseModel):
    account_id: Optional[str] = None  # None for Consolidated
    bank_name: str
    account_no_masked: str
    account_type: str
    period_from: Optional[date] = None
    period_to: Optional[date] = None
    abb: float
    turnover: float
    emi_count: int
    status: str
    is_consolidated: bool = False

class TransactionResponse(BaseModel):
    id: str
    statement_id: str
    txn_date: date
    value_date: Optional[date] = None
    narration_raw: str
    narration_clean: Optional[str] = None
    ref_no: Optional[str] = None
    utr: Optional[str] = None
    debit: float
    credit: float
    balance: float
    channel: str
    counterparty: Optional[str] = None
    category: str
    confidence: float
    source_page_no: int
    is_duplicate: bool
    is_internal_transfer: bool
    internal_match_id: Optional[str] = None
    statement_bank: Optional[str] = None
    statement_account_masked: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    page_size: int

class EmiAttemptResponse(BaseModel):
    id: str
    attempt_date: date
    amount: float
    status: str  # SUCCESS, RETURNED, PENDING
    return_id: Optional[str] = None
    transaction_id: str
    narration_raw: Optional[str] = None
    source_page_no: Optional[int] = None
    ref_no: Optional[str] = None

class EmiRecordResponse(BaseModel):
    id: str
    lender_name: str
    lender_confidence: str  # CONFIRMED, PROBABLE, POSSIBLE
    mandate_ref: Optional[str] = None
    amount: float
    frequency: str  # MONTHLY, WEEKLY, QUARTERLY, VARIABLE
    first_date: Optional[date] = None
    last_date: Optional[date] = None
    total_attempts: int
    total_success: int
    total_returns: int
    status: str
    latest_mode: str = "NACH"
    latest_date: Optional[date] = None
    masked_account: Optional[str] = None
    bank_name: Optional[str] = None

class EmiDetailResponse(BaseModel):
    emi_record: EmiRecordResponse
    attempts: List[EmiAttemptResponse]
    bounce_rate: float
    last_3_attempts: List[EmiAttemptResponse]
    recovery_info: Optional[Dict[str, Any]] = None

class ReturnRecordResponse(BaseModel):
    id: str
    original_emi_date: Optional[date] = None
    lender_name: str
    emi_amount: float
    return_date: date
    return_amount: float
    return_charge_amount: float
    charge_txn_id: Optional[str] = None
    reason: str
    recovery_status: str
    recovery_txn_id: Optional[str] = None
    source_page_no: int
    original_txn_narration: Optional[str] = None
    return_txn_narration: Optional[str] = None
    ref_no: Optional[str] = None

class MonthlySummaryResponse(BaseModel):
    month: str  # YYYY-MM
    gross_credit: float
    business_turnover: float
    non_business_credit: float
    internal_transfer_credit_excluded: float
    total_debit: float
    net_flow: float
    abb: float
    min_balance: float
    max_balance: float
    min_balance_date: Optional[date] = None
    month_end_balance: float
    negative_days: int
    days_below_5000: int
    days_below_10000: int
    emi_burden: float
    emi_bounce_count: int
    emi_to_turnover_ratio: float = 0.0

class SummaryKpiResponse(BaseModel):
    total_business_turnover: float
    avg_monthly_turnover: float
    total_debit: float
    net_cash_flow: float
    avg_monthly_abb: float
    emi_bounce_count: int
    total_ecs_returns: int
    emi_to_turnover_ratio: float
    total_negative_days: int
    review_queue_count: int
    internal_transfers_excluded: float
    monthly_breakdown: List[MonthlySummaryResponse]
    has_data: bool = True

class ReviewQueueItemResponse(BaseModel):
    id: str
    statement_id: str
    transaction_id: Optional[str] = None
    issue_type: str
    confidence: float
    suggested_value: Optional[Dict[str, Any]] = None
    status: str
    narration_raw: Optional[str] = None
    source_page_no: Optional[int] = None
    amount: Optional[float] = None
    date: Optional[date] = None
    created_at: datetime

class ReviewResolveRequest(BaseModel):
    action: str  # APPROVE, CORRECT, REJECT
    corrected_value: Optional[Dict[str, Any]] = None
    reason: str

class UnderwritingExportResponse(BaseModel):
    export_id: str
    application_id: str
    analysis_version_id: str
    payload: Dict[str, Any]
    status: str
    sent_to_engine_at: datetime

class AnalysisVersionResponse(BaseModel):
    id: str
    version_no: int
    created_by: str
    created_at: datetime
    is_current: bool
    summary: Dict[str, Any]

