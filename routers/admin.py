import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from models import Receipt, UserDevice
from schemas import ActionResponse, AdminReceiptResponse
from services.subscription_service import approve_receipt, ban_user, ensure_subscription, reject_receipt, restore_after_unban


router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/receipts", response_model=list[AdminReceiptResponse])
def list_receipts(db: Session = Depends(get_db)) -> list[AdminReceiptResponse]:
    receipts = db.scalars(select(Receipt).order_by(Receipt.uploaded_at.desc(), Receipt.id.desc())).all()
    response: list[AdminReceiptResponse] = []

    for receipt in receipts:
        subscription = ensure_subscription(db, receipt.user_device)
        response.append(
            AdminReceiptResponse(
                id=receipt.id,
                deviceId=receipt.user_device.device_id,
                planTitle=receipt.tariff_plan.title,
                planCode=receipt.tariff_plan.code,
                amountRub=receipt.amount_rub,
                uploadedAt=receipt.uploaded_at,
                clientSubmittedAt=receipt.client_submitted_at,
                reviewStatus=receipt.review_status,
                emailStatus=receipt.email_status,
                accessStatus=subscription.access_status,
                subscriptionExpiresAt=subscription.ends_at,
                receiptUrl=f"{settings.public_base_url}/uploads/{receipt.stored_file_name}",
                serviceInfo=json.loads(receipt.service_info_json or "{}"),
                adminNote=receipt.admin_note,
            )
        )

    return response


@router.post("/receipts/{receipt_id}/approve", response_model=ActionResponse)
def approve_uploaded_receipt(receipt_id: int, db: Session = Depends(get_db)) -> ActionResponse:
    receipt = db.get(Receipt, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    subscription = approve_receipt(db, receipt)
    db.commit()
    db.refresh(subscription)

    return ActionResponse(
        message="Receipt approved. User access is active.",
        deviceId=receipt.user_device.device_id,
        accessStatus=subscription.access_status,
    )


@router.post("/receipts/{receipt_id}/reject", response_model=ActionResponse)
def reject_uploaded_receipt(receipt_id: int, db: Session = Depends(get_db)) -> ActionResponse:
    receipt = db.get(Receipt, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Receipt not found")

    subscription = reject_receipt(db, receipt)
    db.commit()
    db.refresh(subscription)

    return ActionResponse(
        message="Receipt rejected. User access is disabled.",
        deviceId=receipt.user_device.device_id,
        accessStatus=subscription.access_status,
    )


@router.post("/users/{device_id}/ban", response_model=ActionResponse)
def ban_device(device_id: str, db: Session = Depends(get_db)) -> ActionResponse:
    device = db.scalar(select(UserDevice).where(UserDevice.device_id == device_id))
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    subscription = ban_user(db, device)
    db.commit()
    db.refresh(subscription)

    return ActionResponse(
        message="User banned. VPN access disabled immediately.",
        deviceId=device.device_id,
        accessStatus=subscription.access_status,
    )


@router.post("/users/{device_id}/unban", response_model=ActionResponse)
def unban_device(device_id: str, db: Session = Depends(get_db)) -> ActionResponse:
    device = db.scalar(select(UserDevice).where(UserDevice.device_id == device_id))
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    subscription = restore_after_unban(db, device)
    db.commit()
    db.refresh(subscription)

    return ActionResponse(
        message="User unbanned. Access status recalculated from the latest receipt.",
        deviceId=device.device_id,
        accessStatus=subscription.access_status,
    )
