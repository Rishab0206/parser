from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date

class TransactionBase(BaseModel):
    txn_date: date
    value_date: Optional[date] = None
    narration_raw: str
    narration_clean: Optional[str] = None
    ref_no: Optional[str] = None
    utr: Optional[str] = None
    debit: float = 0.0
    credit: float = 0.0
    balance: float
    channel: str = "OTHER"
    counterparty: Optional[str] = None
    category: str = "UNCATEGORIZED"
    confidence: float = 100.0
    source_page_no: int = 1
    is_duplicate: bool = False
    is_internal_transfer: bool = False
    internal_match_id: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: str
    statement_id: str
    statement_bank: Optional[str] = None
    statement_account_masked: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

