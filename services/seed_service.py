from sqlalchemy.orm import Session

from models import TariffPlan


DEFAULT_PLANS = [
    {
        "code": "plan_1m",
        "title": "1 месяц",
        "description": "Базовый доступ к VPN на 30 дней",
        "amount_rub": 100,
        "duration_days": 30,
        "is_featured": False,
        "sort_order": 1,
    },
    {
        "code": "plan_3m",
        "title": "3 месяца",
        "description": "Самый выгодный тариф для постоянного использования",
        "amount_rub": 250,
        "duration_days": 90,
        "is_featured": True,
        "sort_order": 2,
    },
]


def seed_tariff_plans(db: Session) -> None:
    for payload in DEFAULT_PLANS:
        plan = db.query(TariffPlan).filter(TariffPlan.code == payload["code"]).one_or_none()
        if plan is None:
            db.add(TariffPlan(**payload))
            continue

        plan.title = payload["title"]
        plan.description = payload["description"]
        plan.amount_rub = payload["amount_rub"]
        plan.duration_days = payload["duration_days"]
        plan.is_featured = payload["is_featured"]
        plan.sort_order = payload["sort_order"]
        plan.is_active = True

    db.commit()
