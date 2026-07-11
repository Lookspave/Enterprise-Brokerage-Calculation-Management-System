from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ebcms.config import get_settings
from ebcms.core.enums import TradeStatus
from ebcms.models import AuditLog, BrokerageResult, BrokerageRule, Client, Product, Trade
from ebcms.services.brokerage_engine import (
    BrokerageEngine,
    CalculationRule,
    CalculationTrade,
    NoApplicableRuleError,
    TaxProfile,
)


class CalculationError(ValueError):
    """Raised when a trade cannot be calculated."""


@dataclass(frozen=True)
class BatchCalculationFailure:
    trade_id: str
    reason: str


@dataclass(frozen=True)
class BatchCalculationResult:
    total_trades: int
    calculated_trade_ids: list[str]
    failures: list[BatchCalculationFailure]
    total_brokerage: Decimal
    total_charges: Decimal


def calculate_trade_brokerage(
    *,
    trade: Trade,
    calculated_by: str,
    db: Session,
    commit: bool = True,
) -> BrokerageResult:
    if trade.status == TradeStatus.REJECTED.value:
        raise CalculationError(f"Rejected trade cannot be calculated: {trade.rejection_reason}")

    client = db.get(Client, trade.client_id)
    product = db.get(Product, trade.product_id)
    if not client or not product:
        raise CalculationError("Trade reference data is incomplete.")

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
        raise CalculationError(str(exc)) from exc

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
        calculated_by=calculated_by,
    )
    trade.status = TradeStatus.CALCULATED.value
    db.add(result)
    db.add(
        AuditLog(
            entity_type="BROKERAGE_RESULT",
            entity_id=trade.trade_id,
            action="CALCULATE",
            new_value=f"rule_id={breakdown.rule_id}; total_charges={breakdown.total_charges}",
            user_id=calculated_by,
        )
    )

    if commit:
        db.commit()
        db.refresh(result)

    return result


def calculate_validated_trades(
    *,
    trades: list[Trade],
    calculated_by: str,
    db: Session,
) -> BatchCalculationResult:
    calculated_trade_ids: list[str] = []
    failures: list[BatchCalculationFailure] = []
    total_brokerage = Decimal("0.00")
    total_charges = Decimal("0.00")

    for trade in trades:
        try:
            result = calculate_trade_brokerage(
                trade=trade,
                calculated_by=calculated_by,
                db=db,
                commit=False,
            )
        except CalculationError as exc:
            failures.append(BatchCalculationFailure(trade_id=trade.trade_id, reason=str(exc)))
            continue

        calculated_trade_ids.append(trade.trade_id)
        total_brokerage += result.brokerage
        total_charges += result.total_charges

    db.commit()

    return BatchCalculationResult(
        total_trades=len(trades),
        calculated_trade_ids=calculated_trade_ids,
        failures=failures,
        total_brokerage=total_brokerage,
        total_charges=total_charges,
    )


def select_validated_trades_for_batch(
    *,
    db: Session,
    import_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    calculate_all_validated: bool = False,
) -> list[Trade]:
    statement = select(Trade).where(Trade.status == TradeStatus.VALIDATED.value)

    if import_id is not None:
        statement = statement.where(Trade.import_id == import_id)
    if date_from is not None:
        statement = statement.where(Trade.trade_date >= date_from)
    if date_to is not None:
        statement = statement.where(Trade.trade_date <= date_to)
    if not calculate_all_validated and import_id is None and date_from is None and date_to is None:
        return []

    return list(db.scalars(statement.order_by(Trade.trade_date, Trade.trade_id)))


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
