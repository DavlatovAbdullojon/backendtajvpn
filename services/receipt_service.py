from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from config import settings
from models import EmailDeliveryStatus, Receipt, TariffPlan
from services.device_service import get_or_create_device
from services.email_service import send_receipt_email
from services.subscription_service import apply_provisional_access


def _save_upload(receipt_file: UploadFile) -> tuple[str, Path]:
    extension = Path(receipt_file.filename or "").suffix or ".bin"
    stored_name = f"{uuid4().hex}{extension.lower()}"
    target_path = settings.upload_path / stored_name
    settings.upload_path.mkdir(parents=True, exist_ok=True)

    with target_path.open("wb") as output:
        while chunk := receipt_file.file.read(1024 * 1024):
            output.write(chunk)

    return stored_name, target_path


def create_receipt_upload(
    db: Session,
    *,
    device_id: str,
    plan_id: int,
    amount_rub: int,
    receipt_file: UploadFile,
    client_submitted_at,
    service_info: dict,
):
    device = get_or_create_device(
        db,
        device_id=device_id,
        platform=service_info.get("platform") or "android",
        app_version=service_info.get("appVersion"),
        device_model=service_info.get("deviceModel"),
    )

    plan = db.get(TariffPlan, plan_id)
    if plan is None or not plan.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tariff plan not found")

    if amount_rub != plan.amount_rub:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Amount does not match tariff plan")

    stored_name, stored_path = _save_upload(receipt_file)

    try:
        receipt = Receipt(
            user_device_id=device.id,
            tariff_plan_id=plan.id,
            amount_rub=amount_rub,
            original_file_name=receipt_file.filename or "receipt.bin",
            stored_file_name=stored_name,
            file_path=str(stored_path),
            client_submitted_at=client_submitted_at,
            service_info_json=json.dumps(service_info, ensure_ascii=False),
        )
        db.add(receipt)
        db.flush()

        subscription = apply_provisional_access(
            db,
            device=device,
            plan=plan,
            receipt_id=receipt.id,
        )
        db.commit()
        db.refresh(receipt)
        db.refresh(subscription)
    except Exception:
        db.rollback()
        stored_path.unlink(missing_ok=True)
        raise

    summary_lines = [
        f"Device ID: {device.device_id}",
        f"Platform: {device.platform}",
        f"App version: {device.app_version or '-'}",
        f"Device model: {device.device_model or '-'}",
        f"Tariff: {plan.title} ({plan.code})",
        f"Amount: {receipt.amount_rub} RUB",
        f"Uploaded at: {receipt.uploaded_at.isoformat()}",
        f"Client submitted at: {receipt.client_submitted_at.isoformat() if receipt.client_submitted_at else '-'}",
        f"Access status after upload: {subscription.access_status.value}",
        f"Service info: {json.dumps(service_info, ensure_ascii=False)}",
    ]

    email_status, email_message = send_receipt_email(
        device=device,
        receipt=receipt,
        summary_lines=summary_lines,
    )
    receipt.email_status = email_status
    if email_status == EmailDeliveryStatus.FAILED:
        receipt.admin_note = email_message
    db.commit()
    db.refresh(receipt)
    db.refresh(subscription)

    return receipt, subscription, plan, email_message
