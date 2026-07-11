from enum import StrEnum


class BrokerageType(StrEnum):
    PERCENTAGE = "PERCENTAGE"
    FLAT = "FLAT"


class TradeSide(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class TradeStatus(StrEnum):
    PENDING = "PENDING"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    CALCULATED = "CALCULATED"


class UserRole(StrEnum):
    ADMIN = "ADMIN"
    OPERATIONS = "OPERATIONS"
    BROKERAGE_MANAGER = "BROKERAGE_MANAGER"
    FINANCE = "FINANCE"
    RISK = "RISK"
    COMPLIANCE = "COMPLIANCE"
    RELATIONSHIP_MANAGER = "RELATIONSHIP_MANAGER"
