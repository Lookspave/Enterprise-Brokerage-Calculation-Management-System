from datetime import date, datetime, time
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ebcms.api.dependencies import require_roles
from ebcms.core.enums import TradeStatus, UserRole
from ebcms.database import get_db
from ebcms.models import (
    AuditLog,
    BrokerageResult,
    BrokerageRule,
    Client,
    Product,
    Trade,
    TradeImportBatch,
    TradeImportReject,
    User,
)
from ebcms.schemas import AuditLogPage, DashboardSummary

router = APIRouter(tags=["operations"])

AUDIT_ROLES = {
    UserRole.ADMIN.value,
    UserRole.RISK.value,
    UserRole.COMPLIANCE.value,
}

DASHBOARD_ROLES = {
    UserRole.ADMIN.value,
    UserRole.OPERATIONS.value,
    UserRole.BROKERAGE_MANAGER.value,
    UserRole.FINANCE.value,
    UserRole.RISK.value,
    UserRole.COMPLIANCE.value,
}


@router.get("/audit", response_model=AuditLogPage)
def list_audit_logs(
    entity_type: str | None = None,
    entity_id: str | None = None,
    action: str | None = None,
    user_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*AUDIT_ROLES)),
) -> AuditLogPage:
    statement = select(AuditLog)
    count_statement = select(func.count(AuditLog.audit_id))

    filters = []
    if entity_type:
        filters.append(AuditLog.entity_type == entity_type.upper())
    if entity_id:
        filters.append(AuditLog.entity_id == entity_id)
    if action:
        filters.append(AuditLog.action == action.upper())
    if user_id:
        filters.append(AuditLog.user_id == user_id)
    if date_from:
        filters.append(AuditLog.created_at >= datetime.combine(date_from, time.min))
    if date_to:
        filters.append(AuditLog.created_at <= datetime.combine(date_to, time.max))

    for condition in filters:
        statement = statement.where(condition)
        count_statement = count_statement.where(condition)

    total = db.scalar(count_statement) or 0
    items = list(
        db.scalars(
            statement.order_by(AuditLog.created_at.desc(), AuditLog.audit_id.desc())
            .offset(offset)
            .limit(limit)
        )
    )
    return AuditLogPage(total=total, limit=limit, offset=offset, items=items)


@router.get("/dashboard", response_model=DashboardSummary)
def get_dashboard(
    business_date: date | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(*DASHBOARD_ROLES)),
) -> DashboardSummary:
    selected_date = business_date or date.today()
    start_of_day = datetime.combine(selected_date, time.min)
    end_of_day = datetime.combine(selected_date, time.max)

    recent_audit = list(
        db.scalars(
            select(AuditLog)
            .order_by(AuditLog.created_at.desc(), AuditLog.audit_id.desc())
            .limit(5)
        )
    )

    return DashboardSummary(
        business_date=selected_date,
        today_trades=_trade_count(db, Trade.trade_date == selected_date),
        today_brokerage=_money(
            db.scalar(
                select(func.coalesce(func.sum(BrokerageResult.total_charges), 0))
                .join(Trade, Trade.trade_id == BrokerageResult.trade_id)
                .where(Trade.trade_date == selected_date)
            )
        ),
        pending_trades=_trade_count(db, Trade.status == TradeStatus.PENDING.value),
        validated_trades=_trade_count(db, Trade.status == TradeStatus.VALIDATED.value),
        calculated_trades=_trade_count(db, Trade.status == TradeStatus.CALCULATED.value),
        rejected_trades=_trade_count(db, Trade.status == TradeStatus.REJECTED.value),
        imports_today=db.scalar(
            select(func.count(TradeImportBatch.import_id)).where(
                TradeImportBatch.created_at >= start_of_day,
                TradeImportBatch.created_at <= end_of_day,
            )
        )
        or 0,
        rejected_import_rows_today=db.scalar(
            select(func.count(TradeImportReject.rejection_id)).where(
                TradeImportReject.created_at >= start_of_day,
                TradeImportReject.created_at <= end_of_day,
            )
        )
        or 0,
        active_rules=db.scalar(
            select(func.count(BrokerageRule.rule_id)).where(BrokerageRule.is_active.is_(True))
        )
        or 0,
        active_clients=db.scalar(select(func.count(Client.client_id)).where(Client.is_active.is_(True)))
        or 0,
        active_products=db.scalar(
            select(func.count(Product.product_id)).where(Product.is_active.is_(True))
        )
        or 0,
        recent_audit=recent_audit,
    )


def _trade_count(db: Session, *conditions: object) -> int:
    statement = select(func.count(Trade.trade_id))
    for condition in conditions:
        statement = statement.where(condition)
    return db.scalar(statement) or 0


def _money(value: Decimal | int | float | str | None) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))
