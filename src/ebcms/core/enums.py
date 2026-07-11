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

