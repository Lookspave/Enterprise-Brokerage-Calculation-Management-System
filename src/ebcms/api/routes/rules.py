from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ebcms.api.dependencies import require_roles
from ebcms.core.enums import UserRole
from ebcms.database import get_db
from ebcms.models import AuditLog, BrokerageRule, User
from ebcms.schemas import RuleCreate, RuleRead, RuleUpdate

router = APIRouter(tags=["brokerage rules"])


@router.post("/rules", response_model=RuleRead, status_code=status.HTTP_201_CREATED)
def create_rule(
    payload: RuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN.value, UserRole.BROKERAGE_MANAGER.value)
    ),
) -> BrokerageRule:
    payload_dict = payload.model_dump(exclude={"change_reason"})
    payload_dict["product_code"] = payload_dict["product_code"].upper()
    payload_dict["client_type"] = payload_dict["client_type"].upper()
    payload_dict["exchange"] = payload_dict["exchange"].upper()
    payload_dict["country"] = payload_dict["country"].upper()
    payload_dict["currency"] = payload_dict["currency"].upper()
    payload_dict["trade_side"] = str(payload_dict["trade_side"]).upper()
    payload_dict["brokerage_type"] = str(payload_dict["brokerage_type"]).upper()

    rule = BrokerageRule(**payload_dict)
    db.add(rule)
    db.flush()
    db.add(
        AuditLog(
            entity_type="BROKERAGE_RULE",
            entity_id=str(rule.rule_id),
            action="CREATE",
            new_value=str(payload_dict),
            user_id=current_user.username,
            change_reason=payload.change_reason,
        )
    )
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/rules", response_model=list[RuleRead])
def list_rules(
    active_only: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN.value,
            UserRole.OPERATIONS.value,
            UserRole.BROKERAGE_MANAGER.value,
            UserRole.FINANCE.value,
            UserRole.COMPLIANCE.value,
        )
    ),
) -> list[BrokerageRule]:
    statement = select(BrokerageRule)
    if active_only:
        statement = statement.where(BrokerageRule.is_active.is_(True))
    return list(db.scalars(statement.order_by(BrokerageRule.priority.desc(), BrokerageRule.rule_id)))


@router.put("/rules/{rule_id}", response_model=RuleRead)
def update_rule(
    rule_id: int,
    payload: RuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN.value, UserRole.BROKERAGE_MANAGER.value)
    ),
) -> BrokerageRule:
    rule = db.get(BrokerageRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")

    old_value = _rule_snapshot(rule)
    updates = payload.model_dump(exclude_unset=True, exclude={"change_reason"})
    for field, value in updates.items():
        if isinstance(value, str) and field not in {"expiry_date"}:
            value = value.upper()
        setattr(rule, field, value)

    db.add(
        AuditLog(
            entity_type="BROKERAGE_RULE",
            entity_id=str(rule.rule_id),
            action="UPDATE",
            old_value=str(old_value),
            new_value=str(_rule_snapshot(rule)),
            user_id=current_user.username,
            change_reason=payload.change_reason,
        )
    )
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}", response_model=RuleRead)
def deactivate_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN.value, UserRole.BROKERAGE_MANAGER.value)
    ),
) -> BrokerageRule:
    rule = db.get(BrokerageRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found.")
    old_value = _rule_snapshot(rule)
    rule.is_active = False
    db.add(
        AuditLog(
            entity_type="BROKERAGE_RULE",
            entity_id=str(rule.rule_id),
            action="DEACTIVATE",
            old_value=str(old_value),
            new_value=str(_rule_snapshot(rule)),
            user_id=current_user.username,
        )
    )
    db.commit()
    db.refresh(rule)
    return rule


def _rule_snapshot(rule: BrokerageRule) -> dict[str, object]:
    return {
        "rule_id": rule.rule_id,
        "product_code": rule.product_code,
        "client_type": rule.client_type,
        "exchange": rule.exchange,
        "country": rule.country,
        "currency": rule.currency,
        "trade_side": rule.trade_side,
        "brokerage_type": rule.brokerage_type,
        "brokerage_value": str(rule.brokerage_value),
        "effective_date": str(rule.effective_date),
        "expiry_date": str(rule.expiry_date) if rule.expiry_date else None,
        "priority": rule.priority,
        "is_active": rule.is_active,
    }
