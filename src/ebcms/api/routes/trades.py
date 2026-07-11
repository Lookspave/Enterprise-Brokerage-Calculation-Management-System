from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from ebcms.config import get_settings
from ebcms.core.enums import TradeStatus
from ebcms.database import get_db
from ebcms.models import AuditLog, BrokerageResult, BrokerageRule, Client, Product, Trade
from ebcms.schemas import BrokerageRead, CalculationRequest, TradeCreate, TradeRead
from ebcms.services.brokerage_engine import (
    BrokerageEngine,
    CalculationRule,
    CalculationTrade,
    NoApplicableRuleError,
    TaxProfile,
)
from ebcms.services.validation import validate_trade_record

router = APIRouter(tags=["trades and calculations"])


@router.post("/trade", response_model=TradeRead, status_code=status.HTTP_201_CREATED)
def create_trade(payload: TradeCreate, db: Session = Depends(get_db)) -> Trade:
    if db.get(Trade, payload.trade_id):
        raise HTTPException(status_code=409, detail="Duplicate trade ID.")

    client = db.get(Client, payload.client_id)
    product = db.get(Product, payload.product_id)
    settings = get_settings()
    validation = validate_trade_record(
        trade_id=payload.trade_id,
        client_exists=bool(client and client.is_active),
        product_exists=bool(product and product.is_active),
        duplicate_trade_id=False,
        quantity=payload.quantity,
        price=payload.price,
        currency=payload.currency,
        trade_side=str(payload.trade_side),
        trade_date=payload.trade_date,
        allowed_currencies=settings.currency_set,
    )

    trade = Trade(
        **payload.model_dump(exclude={"trade_side"}),
        trade_side=str(payload.trade_side).upper(),
        currency=payload.currency.upper(),
        exchange=payload.exchange.upper(),
        status=TradeStatus.VALIDATED.value if validation.is_valid else TradeStatus.REJECTED.value,
        rejection_reason="; ".join(validation.issues) if validation.issues else None,
    )
    db.add(trade)
    db.add(
        AuditLog(
            entity_type="TRADE",
            entity_id=trade.trade_id,
            action="CREATE",
            new_value=f"status={trade.status}",
            change_reason=trade.rejection_reason,
        )
    )
    db.commit()
    db.refresh(trade)
    return trade


@router.get("/trade/{trade_id}", response_model=TradeRead)
def get_trade(trade_id: str, db: Session = Depends(get_db)) -> Trade:
    trade = db.get(Trade, trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found.")
    return trade


@router.post("/calculate", response_model=BrokerageRead)
def calculate_trade(payload: CalculationRequest, db: Session = Depends(get_db)) -> BrokerageResult:
    trade = db.get(Trade, payload.trade_id)
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found.")
    if trade.status == TradeStatus.REJECTED.value:
        raise HTTPException(status_code=422, detail=f"Rejected trade cannot be calculated: {trade.rejection_reason}")

    client = db.get(Client, trade.client_id)
    product = db.get(Product, trade.product_id)
    if not client or not product:
        raise HTTPException(status_code=422, detail="Trade reference data is incomplete.")

    rules = list(db.scalars(select(BrokerageRule).where(BrokerageRule.is_active.is_(True))))
    engine = BrokerageEngine(_tax_profile_from_settings())
    calculation_trade = CalculationTrade(
        trade_id=trade.trade_id,
        product_code=product.product_code,
        client_type=client.client_type,
        exchange=trade.exchange,
        country=client.country,
        currency=trade.currency,
        trade_side=trade.trade_side,
        quantity=trade.quantity,
        price=trade.price,
        trade_date=trade.trade_date,
    )

    try:
        rule = engine.find_applicable_rule(calculation_trade, [_to_calculation_rule(rule) for rule in rules])
    except NoApplicableRuleError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    breakdown = engine.calculate(calculation_trade, rule)
    result = BrokerageResult(
        trade_id=breakdown.trade_id,
        rule_id=breakdown.rule_id,
        trade_value=breakdown.trade_value,
        brokerage=breakdown.brokerage,
        gst=breakdown.gst,
        stt=breakdown.stt,
        exchange_txn_charge=breakdown.exchange_txn_charge,
        sebi_charge=breakdown.sebi_charge,
        total_charges=breakdown.total_charges,
        calculated_by=payload.calculated_by,
    )
    trade.status = TradeStatus.CALCULATED.value
    db.add(result)
    db.add(
        AuditLog(
            entity_type="BROKERAGE_RESULT",
            entity_id=trade.trade_id,
            action="CALCULATE",
            new_value=f"rule_id={breakdown.rule_id}; total_charges={breakdown.total_charges}",
            user_id=payload.calculated_by,
        )
    )
    db.commit()
    db.refresh(result)
    return result


@router.get("/brokerage/{trade_id}", response_model=BrokerageRead)
def get_latest_brokerage(trade_id: str, db: Session = Depends(get_db)) -> BrokerageResult:
    result = db.scalar(
        select(BrokerageResult)
        .where(BrokerageResult.trade_id == trade_id)
        .order_by(desc(BrokerageResult.calculated_at), desc(BrokerageResult.result_id))
    )
    if not result:
        raise HTTPException(status_code=404, detail="Brokerage result not found.")
    return result


def _tax_profile_from_settings() -> TaxProfile:
    settings = get_settings()
    return TaxProfile(
        gst_rate=settings.default_gst_rate,
        stt_rate=settings.default_stt_rate,
        exchange_txn_rate=settings.default_exchange_txn_rate,
        sebi_rate=settings.default_sebi_rate,
    )


def _to_calculation_rule(rule: BrokerageRule) -> CalculationRule:
    return CalculationRule(
        rule_id=rule.rule_id,
        product_code=rule.product_code,
        client_type=rule.client_type,
        exchange=rule.exchange,
        country=rule.country,
        currency=rule.currency,
        trade_side=rule.trade_side,
        brokerage_type=rule.brokerage_type,
        brokerage_value=rule.brokerage_value,
        effective_date=rule.effective_date,
        expiry_date=rule.expiry_date,
        priority=rule.priority,
    )

