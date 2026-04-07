from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import AccessStatus, Receipt, ReceiptReviewStatus, Subscription, TariffPlan, UserDevice, utcnow


def allows_vpn(access_status: AccessStatus) -> bool:
    return access_status in {AccessStatus.PROVISIONAL, AccessStatus.ACTIVE}


def ensure_subscription(db: Session, device: UserDevice) -> Subscription:
    subscription = db.scalar(select(Subscription).where(Subscription.user_device_id == device.id))
    if subscription is None:
        subscription = Subscription(
            user_device_id=device.id,
            access_status=AccessStatus.INACTIVE,
        )
        db.add(subscription)
        db.flush()
    return subscription


def get_latest_receipt(db: Session, device: UserDevice) -> Receipt | None:
    return db.scalar(
        select(Receipt)
        .where(Receipt.user_device_id == device.id)
        .order_by(Receipt.uploaded_at.desc(), Receipt.id.desc())
    )


def apply_provisional_access(
    db: Session,
    *,
    device: UserDevice,
    plan: TariffPlan,
    receipt_id: int,
) -> Subscription:
    subscription = ensure_subscription(db, device)
    if subscription.access_status == AccessStatus.BANNED:
        subscription.last_receipt_id = receipt_id
        db.flush()
        return subscription

    now = utcnow()
    subscription.tariff_plan_id = plan.id
    subscription.access_status = AccessStatus.PROVISIONAL
    subscription.starts_at = now
    subscription.ends_at = now + timedelta(days=plan.duration_days)
    subscription.last_receipt_id = receipt_id
    db.flush()
    return subscription


def approve_receipt(db: Session, receipt: Receipt) -> Subscription:
    subscription = ensure_subscription(db, receipt.user_device)
    now = utcnow()
    receipt.review_status = ReceiptReviewStatus.APPROVED
    if subscription.access_status != AccessStatus.BANNED:
        subscription.tariff_plan_id = receipt.tariff_plan_id
        subscription.last_receipt_id = receipt.id
        subscription.access_status = AccessStatus.ACTIVE
        if subscription.starts_at is None:
            subscription.starts_at = now
        if subscription.ends_at is None or subscription.ends_at <= now:
            subscription.ends_at = max(subscription.starts_at, now) + timedelta(days=receipt.tariff_plan.duration_days)
    db.flush()
    return subscription


def reject_receipt(db: Session, receipt: Receipt, admin_note: str | None = None) -> Subscription:
    subscription = ensure_subscription(db, receipt.user_device)
    receipt.review_status = ReceiptReviewStatus.REJECTED
    receipt.admin_note = admin_note
    if subscription.access_status != AccessStatus.BANNED:
        subscription.access_status = AccessStatus.REJECTED
        subscription.ends_at = utcnow()
        subscription.last_receipt_id = receipt.id
    db.flush()
    return subscription


def ban_user(db: Session, device: UserDevice) -> Subscription:
    subscription = ensure_subscription(db, device)
    subscription.access_status = AccessStatus.BANNED
    db.flush()
    return subscription


def restore_after_unban(db: Session, device: UserDevice) -> Subscription:
    subscription = ensure_subscription(db, device)
    latest_receipt = get_latest_receipt(db, device)
    now = utcnow()

    if latest_receipt and latest_receipt.review_status == ReceiptReviewStatus.APPROVED and subscription.ends_at and subscription.ends_at > now:
        subscription.access_status = AccessStatus.ACTIVE
    elif latest_receipt and latest_receipt.review_status == ReceiptReviewStatus.PENDING and subscription.ends_at and subscription.ends_at > now:
        subscription.access_status = AccessStatus.PROVISIONAL
    else:
        subscription.access_status = AccessStatus.INACTIVE
        if subscription.ends_at and subscription.ends_at <= now:
            subscription.tariff_plan_id = None

    db.flush()
    return subscription


def subscription_message(subscription: Subscription) -> str:
    messages = {
        AccessStatus.INACTIVE: "Доступ не активирован. Загрузите чек оплаты.",
        AccessStatus.PROVISIONAL: "Чек получен. Доступ включён временно до проверки.",
        AccessStatus.ACTIVE: "Подписка активна. Доступ к VPN разрешён.",
        AccessStatus.REJECTED: "Чек отклонён. Доступ к VPN отключён.",
        AccessStatus.BANNED: "Устройство заблокировано. Доступ к VPN отключён.",
    }
    return messages[subscription.access_status]
