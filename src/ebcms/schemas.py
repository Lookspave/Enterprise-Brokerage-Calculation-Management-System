from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from ebcms.core.enums import BrokerageType, TradeSide, TradeStatus, UserRole


class ClientCreate(BaseModel):
    client_id: str = Field(min_length=1, max_length=40)
    client_name: str = Field(min_length=1, max_length=200)
    client_type: str = Field(min_length=1, max_length=40)
    country: str = Field(default="IN", min_length=2, max_length=40)


class ClientRead(ClientCreate):
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    product_id: str = Field(min_length=1, max_length=40)
    product_code: str = Field(min_length=1, max_length=40)
    product_name: str = Field(min_length=1, max_length=200)
    asset_class: str = Field(min_length=1, max_length=80)


class ProductRead(ProductCreate):
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class AccessToken(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=80)
    email: str = Field(min_length=5, max_length=255)
    full_name: str = Field(min_length=1, max_length=200)
    role: UserRole
    password: str = Field(min_length=8, max_length=128)


class UserRead(BaseModel):
    user_id: int
    username: str
    email: str
    full_name: str
    role: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class TradeCreate(BaseModel):
    trade_id: str = Field(min_length=1, max_length=80)
    client_id: str = Field(min_length=1, max_length=40)
    product_id: str = Field(min_length=1, max_length=40)
    quantity: Decimal = Field(gt=Decimal("0"))
    price: Decimal = Field(gt=Decimal("0"))
    currency: str = Field(min_length=3, max_length=3)
    exchange: str = Field(min_length=1, max_length=30)
    trade_side: TradeSide
    trade_date: date


class TradeRead(TradeCreate):
    status: TradeStatus | str
    rejection_reason: str | None = None
    model_config = ConfigDict(from_attributes=True)


class RuleCreate(BaseModel):
    product_code: str = Field(min_length=1, max_length=40)
    client_type: str = Field(min_length=1, max_length=40)
    exchange: str = Field(min_length=1, max_length=30)
    country: str = Field(default="IN", min_length=2, max_length=40)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    trade_side: TradeSide | str = "ANY"
    brokerage_type: BrokerageType
    brokerage_value: Decimal = Field(gt=Decimal("0"))
    effective_date: date
    expiry_date: date | None = None
    priority: int = 100
    change_reason: str | None = None


class RuleUpdate(BaseModel):
    product_code: str | None = None
    client_type: str | None = None
    exchange: str | None = None
    country: str | None = None
    currency: str | None = None
    trade_side: TradeSide | str | None = None
    brokerage_type: BrokerageType | None = None
    brokerage_value: Decimal | None = Field(default=None, gt=Decimal("0"))
    effective_date: date | None = None
    expiry_date: date | None = None
    priority: int | None = None
    is_active: bool | None = None
    change_reason: str | None = None


class RuleRead(BaseModel):
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
    expiry_date: date | None
    priority: int
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class CalculationRequest(BaseModel):
    trade_id: str
    calculated_by: str = "api"


class BatchCalculationRequest(BaseModel):
    import_id: int | None = None
    date_from: date | None = None
    date_to: date | None = None
    calculate_all_validated: bool = False
    calculated_by: str = "batch-api"


class BatchCalculationFailureRead(BaseModel):
    trade_id: str
    reason: str


class BatchCalculationSummary(BaseModel):
    total_trades: int
    calculated_count: int
    failed_count: int
    total_brokerage: Decimal
    total_charges: Decimal
    calculated_trade_ids: list[str]
    failures: list[BatchCalculationFailureRead]


class BrokerageRead(BaseModel):
    result_id: int
    trade_id: str
    rule_id: int
    trade_value: Decimal
    brokerage: Decimal
    gst: Decimal
    stt: Decimal
    exchange_txn_charge: Decimal
    sebi_charge: Decimal
    total_charges: Decimal
    calculated_by: str
    calculated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TradeImportRejectedRow(BaseModel):
    row_number: int
    trade_id: str | None = None
    reason: str
    raw_payload: dict[str, object]


class TradeImportSummary(BaseModel):
    import_id: int
    filename: str
    source_type: str
    status: str
    total_rows: int
    accepted_rows: int
    rejected_rows: int
    imported_trade_ids: list[str]
    rejected_records: list[TradeImportRejectedRow]


class TradeImportRejectionRead(BaseModel):
    rejection_id: int
    import_id: int
    row_number: int
    trade_id: str | None = None
    reason: str
    raw_payload: dict[str, object]
    created_at: datetime
