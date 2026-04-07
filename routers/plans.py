from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import TariffPlan
from schemas import TariffPlanResponse


router = APIRouter(tags=["plans"])


@router.get("/plans", response_model=list[TariffPlanResponse])
def get_plans(db: Session = Depends(get_db)) -> list[TariffPlanResponse]:
    plans = db.scalars(
        select(TariffPlan)
        .where(TariffPlan.is_active.is_(True))
        .order_by(TariffPlan.sort_order.asc(), TariffPlan.id.asc())
    ).all()
    return [TariffPlanResponse.model_validate(plan) for plan in plans]
