from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, CurrentUser, verify_application_access
from app.services.gst_service import GstPanService

router = APIRouter(prefix="/api/gst", tags=["GST & PAN Intelligence"])

class GstLookupRequest(BaseModel):
    query: str = Field(..., description="10-digit PAN or 15-digit GSTIN")
    application_id: Optional[str] = None
    customer_name: Optional[str] = None
    target_state: Optional[str] = None

@router.post("/lookup")
def lookup_gst_or_pan(
    payload: GstLookupRequest,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user)
):
    cust_name = payload.customer_name

    # If application_id provided, verify access and autofill customer name if missing
    if payload.application_id:
        app_obj = verify_application_access(payload.application_id, current_user, db)
        if not cust_name and app_obj.customer:
            cust_name = app_obj.customer.name

    result = GstPanService.analyze_query(
        payload.query,
        customer_name=cust_name,
        target_state=payload.target_state
    )
    if not result.get("valid"):
        raise HTTPException(status_code=400, detail=result.get("error", "Invalid PAN/GST format"))
    
    return result
