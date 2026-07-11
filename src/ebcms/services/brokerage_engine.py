from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable

from ebcms.core.enums import BrokerageType

MONEY = Decimal("0.01")


@dataclass(frozen=True)
class CalculationTrade:
    trade_id: str
    product_code: str
    client_type: str
    exchange: str
    country: str
    currency: str
    trade_side: str
    quantity: Decimal
    price: Decimal
    trade_date: date


@dataclass(frozen=True)
class CalculationRule:
    rule_id: int
    product_code: str
    client_type: str
    exchange: str
    country: str
    currency: str
    trade_side: str
    brokerage_type: str
    brokerage_value: Decimal
    effective_date: date
    expiry_date: date | None = None
    priority: int = 100


@dataclass(frozen=True)
class TaxProfile:
    gst_rate: Decimal = Decimal("0.18")
    stt_rate: Decimal = Decimal("0.00025")
    exchange_txn_rate: Decimal = Decimal("0.0000325")
    sebi_rate: Decimal = Decimal("0.000001")


@dataclass(frozen=True)
class BrokerageBreakdown:
    trade_id: str
    rule_id: int
    trade_value: Decimal
    brokerage: Decimal
    gst: Decimal
    stt: Decimal
    exchange_txn_charge: Decimal
    sebi_charge: Decimal
    total_charges: Decimal


class NoApplicableRuleError(ValueError):
    """Raised when no active rule matches a validated trade."""


class BrokerageEngine:
    def __init__(self, tax_profile: TaxProfile | None = None) -> None:
        self.tax_profile = tax_profile or TaxProfile()

    def find_applicable_rule(
        self,
        trade: CalculationTrade,
        rules: Iterable[CalculationRule],
    ) -> CalculationRule:
        matches = [rule for rule in rules if self._matches(trade, rule)]
        if not matches:
            raise NoApplicableRuleError(f"No brokerage rule matched trade {trade.trade_id}.")

        return sorted(
            matches,
            key=lambda rule: (
                self._specificity(rule),
                rule.priority,
                rule.effective_date,
                rule.rule_id,
            ),
            reverse=True,
        )[0]

    def calculate(self, trade: CalculationTrade, rule: CalculationRule) -> BrokerageBreakdown:
        trade_value = quantize_money(to_decimal(trade.quantity) * to_decimal(trade.price))
        brokerage = self._calculate_brokerage(trade_value, rule)
        gst = quantize_money(brokerage * self.tax_profile.gst_rate)
        stt = quantize_money(trade_value * self.tax_profile.stt_rate)
        exchange_txn_charge = quantize_money(trade_value * self.tax_profile.exchange_txn_rate)
        sebi_charge = quantize_money(trade_value * self.tax_profile.sebi_rate)
        total_charges = quantize_money(brokerage + gst + stt + exchange_txn_charge + sebi_charge)

        return BrokerageBreakdown(
            trade_id=trade.trade_id,
            rule_id=rule.rule_id,
            trade_value=trade_value,
            brokerage=brokerage,
            gst=gst,
            stt=stt,
            exchange_txn_charge=exchange_txn_charge,
            sebi_charge=sebi_charge,
            total_charges=total_charges,
        )

    def _calculate_brokerage(self, trade_value: Decimal, rule: CalculationRule) -> Decimal:
        brokerage_type = str(rule.brokerage_type).upper()
        if brokerage_type == BrokerageType.PERCENTAGE.value:
            return quantize_money(trade_value * (to_decimal(rule.brokerage_value) / Decimal("100")))
        if brokerage_type == BrokerageType.FLAT.value:
            return quantize_money(rule.brokerage_value)
        raise ValueError(f"Unsupported brokerage type: {rule.brokerage_type}")

    def _matches(self, trade: CalculationTrade, rule: CalculationRule) -> bool:
        return all(
            [
                wildcard_match(rule.product_code, trade.product_code),
                wildcard_match(rule.client_type, trade.client_type),
                wildcard_match(rule.exchange, trade.exchange),
                wildcard_match(rule.country, trade.country),
                wildcard_match(rule.currency, trade.currency),
                wildcard_match(rule.trade_side, trade.trade_side),
                rule.effective_date <= trade.trade_date,
                rule.expiry_date is None or trade.trade_date <= rule.expiry_date,
            ]
        )

    def _specificity(self, rule: CalculationRule) -> int:
        fields = [
            rule.product_code,
            rule.client_type,
            rule.exchange,
            rule.country,
            rule.currency,
            rule.trade_side,
        ]
        return sum(0 if is_wildcard(field) else 1 for field in fields)


def wildcard_match(rule_value: str | None, trade_value: str | None) -> bool:
    if is_wildcard(rule_value):
        return True
    return normalize(rule_value) == normalize(trade_value)


def is_wildcard(value: str | None) -> bool:
    return value is None or normalize(value) in {"ANY", "*", "ALL"}


def normalize(value: str | None) -> str:
    return "" if value is None else str(value).strip().upper()


def to_decimal(value: Decimal | int | float | str) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def quantize_money(value: Decimal | int | float | str) -> Decimal:
    return to_decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)

