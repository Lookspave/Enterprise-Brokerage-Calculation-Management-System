from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ebcms.api.dependencies import require_roles
from ebcms.core.enums import UserRole
from ebcms.database import get_db
from ebcms.models import BrokerageResult, Product, Trade, User

router = APIRouter(tags=["reports"])


@router.get("/reports")
def get_reports(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN.value,
            UserRole.BROKERAGE_MANAGER.value,
            UserRole.FINANCE.value,
            UserRole.RISK.value,
            UserRole.COMPLIANCE.value,
        )
    ),
) -> dict[str, object]:
    base = select(BrokerageResult).join(Trade)
    if date_from:
        base = base.where(Trade.trade_date >= date_from)
    if date_to:
        base = base.where(Trade.trade_date <= date_to)

    result_ids = [row.result_id for row in db.scalars(base)]
    if not result_ids:
        return {
            "trade_count": 0,
            "total_brokerage": "0.00",
            "total_charges": "0.00",
            "by_product": [],
            "by_exchange": [],
        }

    total_row = db.execute(
        select(
            func.count(BrokerageResult.result_id),
            func.coalesce(func.sum(BrokerageResult.brokerage), 0),
            func.coalesce(func.sum(BrokerageResult.total_charges), 0),
        ).where(BrokerageResult.result_id.in_(result_ids))
    ).one()

    by_product = db.execute(
        select(
            Product.product_code,
            func.count(BrokerageResult.result_id),
            func.coalesce(func.sum(BrokerageResult.total_charges), 0),
        )
        .join(Trade, Trade.product_id == Product.product_id)
        .join(BrokerageResult, BrokerageResult.trade_id == Trade.trade_id)
        .where(BrokerageResult.result_id.in_(result_ids))
        .group_by(Product.product_code)
    ).all()

    by_exchange = db.execute(
        select(
            Trade.exchange,
            func.count(BrokerageResult.result_id),
            func.coalesce(func.sum(BrokerageResult.total_charges), 0),
        )
        .join(BrokerageResult, BrokerageResult.trade_id == Trade.trade_id)
        .where(BrokerageResult.result_id.in_(result_ids))
        .group_by(Trade.exchange)
    ).all()

    return {
        "trade_count": total_row[0],
        "total_brokerage": _money(total_row[1]),
        "total_charges": _money(total_row[2]),
        "by_product": [
            {"product_code": row[0], "trade_count": row[1], "total_charges": _money(row[2])}
            for row in by_product
        ],
        "by_exchange": [
            {"exchange": row[0], "trade_count": row[1], "total_charges": _money(row[2])}
            for row in by_exchange
        ],
    }


def _money(value: Decimal | int | float | str) -> str:
    return f"{Decimal(str(value)):.2f}"
