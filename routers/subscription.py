from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import SubscriptionStatusResponse
from services.device_service import get_or_create_device
from services.subscription_service import allows_vpn, ensure_subscription, get_latest_receipt, subscription_message


router = APIRouter(tags=["subscription"])


@router.get("/subscription/status", response_model=SubscriptionStatusResponse)
def get_subscription_status(
    device_id: str = Query(..., alias="deviceId"),
    db: Session = Depends(get_db),
) -> SubscriptionStatusResponse:
    device = get_or_create_device(db, device_id=device_id)
    subscription = ensure_subscription(db, device)
    latest_receipt = get_latest_receipt(db, device)
    db.commit()
    db.refresh(subscription)

    return SubscriptionStatusResponse(
        deviceId=device.device_id,
        accessStatus=subscription.access_status,
        vpnAllowed=allows_vpn(subscription.access_status),
        tariffPlanCode=subscription.tariff_plan.code if subscription.tariff_plan else None,
        tariffPlanTitle=subscription.tariff_plan.title if subscription.tariff_plan else None,
        subscriptionStartedAt=subscription.starts_at,
        subscriptionExpiresAt=subscription.ends_at,
        lastReceiptReviewStatus=latest_receipt.review_status if latest_receipt else None,
        message=subscription_message(subscription),
    )
