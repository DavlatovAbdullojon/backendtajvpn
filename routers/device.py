from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas import DeviceInitRequest, DeviceInitResponse
from services.device_service import get_or_create_device
from services.subscription_service import allows_vpn, ensure_subscription


router = APIRouter(tags=["device"])


@router.post("/device/init", response_model=DeviceInitResponse)
def init_device(payload: DeviceInitRequest, db: Session = Depends(get_db)) -> DeviceInitResponse:
    device = get_or_create_device(
        db,
        device_id=payload.device_id,
        platform=payload.platform,
        app_version=payload.app_version,
        device_model=payload.device_model,
    )
    subscription = ensure_subscription(db, device)
    db.commit()
    db.refresh(device)
    db.refresh(subscription)
    return DeviceInitResponse(
        deviceId=device.device_id,
        accessStatus=subscription.access_status,
        vpnAllowed=allows_vpn(subscription.access_status),
        subscriptionExpiresAt=subscription.ends_at,
    )
