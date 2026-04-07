from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from schemas import ReceiptUploadResponse
from services.receipt_service import create_receipt_upload
from services.subscription_service import allows_vpn, subscription_message


router = APIRouter(tags=["receipts"])


@router.post("/receipts/upload", response_model=ReceiptUploadResponse)
def upload_receipt(
    device_id: str = Form(..., alias="deviceId"),
    plan_id: int = Form(..., alias="planId"),
    amount_rub: int = Form(..., alias="amountRub"),
    submitted_at: datetime | None = Form(default=None, alias="submittedAt"),
    platform: str = Form(default="android"),
    app_version: str | None = Form(default=None, alias="appVersion"),
    device_model: str | None = Form(default=None, alias="deviceModel"),
    notes: str | None = Form(default=None),
    receipt: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ReceiptUploadResponse:
    service_info = {
        "platform": platform,
        "appVersion": app_version,
        "deviceModel": device_model,
        "notes": notes,
    }

    receipt_record, subscription, _, email_message = create_receipt_upload(
        db,
        device_id=device_id,
        plan_id=plan_id,
        amount_rub=amount_rub,
        receipt_file=receipt,
        client_submitted_at=submitted_at,
        service_info=service_info,
    )

    message = subscription_message(subscription)
    if email_message and receipt_record.email_status.value != "sent":
        message = f"{message} Email status: {receipt_record.email_status.value}."

    return ReceiptUploadResponse(
        receiptId=receipt_record.id,
        deviceId=device_id,
        accessStatus=subscription.access_status,
        vpnAllowed=allows_vpn(subscription.access_status),
        reviewStatus=receipt_record.review_status,
        emailStatus=receipt_record.email_status,
        subscriptionExpiresAt=subscription.ends_at,
        message=message,
    )
