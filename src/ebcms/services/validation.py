from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ebcms.core.enums import TradeSide


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    issues: list[str]


def validate_trade_record(
    *,
    trade_id: str,
    client_exists: bool,
    product_exists: bool,
    duplicate_trade_id: bool,
    quantity: Decimal,
    price: Decimal,
    currency: str,
    trade_side: str,
    trade_date: date,
    allowed_currencies: set[str],
) -> ValidationResult:
    issues: list[str] = []

    if not trade_id.strip():
        issues.append("Missing trade ID.")
    if duplicate_trade_id:
        issues.append("Duplicate trade ID.")
    if not client_exists:
        issues.append("Invalid client.")
    if not product_exists:
        issues.append("Invalid product.")
    if quantity <= 0:
        issues.append("Quantity must be greater than zero.")
    if price <= 0:
        issues.append("Price must be greater than zero.")
    if currency.upper() not in allowed_currencies:
        issues.append("Invalid currency.")
    if trade_side.upper() not in {side.value for side in TradeSide}:
        issues.append("Invalid trade side.")
    if trade_date > date.today():
        issues.append("Trade date cannot be in the future.")

    return ValidationResult(is_valid=not issues, issues=issues)

