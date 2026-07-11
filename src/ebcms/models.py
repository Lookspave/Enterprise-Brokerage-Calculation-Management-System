from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Client(Base, TimestampMixin):
    __tablename__ = "client_master"

    client_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    client_name: Mapped[str] = mapped_column(String(200), nullable=False)
    client_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(40), nullable=False, default="IN")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    trades: Mapped[list["Trade"]] = relationship(back_populates="client")


class Product(Base, TimestampMixin):
    __tablename__ = "product_master"

    product_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    product_code: Mapped[str] = mapped_column(String(40), nullable=False, unique=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    asset_class: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    trades: Mapped[list["Trade"]] = relationship(back_populates="product")


class Trade(Base, TimestampMixin):
    __tablename__ = "trade_master"

    trade_id: Mapped[str] = mapped_column(String(80), primary_key=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("client_master.client_id"), index=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("product_master.product_id"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(20, 4), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    trade_side: Mapped[str] = mapped_column(String(10), nullable=False)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDING")
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    client: Mapped[Client] = relationship(back_populates="trades")
    product: Mapped[Product] = relationship(back_populates="trades")
    brokerage_results: Mapped[list["BrokerageResult"]] = relationship(back_populates="trade")


class BrokerageRule(Base, TimestampMixin):
    __tablename__ = "brokerage_rule_master"

    rule_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_code: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    client_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    exchange: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(40), nullable=False, default="IN")
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="INR")
    trade_side: Mapped[str] = mapped_column(String(10), nullable=False, default="ANY")
    brokerage_type: Mapped[str] = mapped_column(String(20), nullable=False)
    brokerage_value: Mapped[Decimal] = mapped_column(Numeric(20, 6), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, default=100)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    brokerage_results: Mapped[list["BrokerageResult"]] = relationship(back_populates="rule")


class BrokerageResult(Base):
    __tablename__ = "brokerage_result"

    result_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    trade_id: Mapped[str] = mapped_column(ForeignKey("trade_master.trade_id"), index=True)
    rule_id: Mapped[int] = mapped_column(ForeignKey("brokerage_rule_master.rule_id"), index=True)
    trade_value: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    brokerage: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    gst: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    stt: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    exchange_txn_charge: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    sebi_charge: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    total_charges: Mapped[Decimal] = mapped_column(Numeric(20, 2), nullable=False)
    calculated_by: Mapped[str] = mapped_column(String(120), nullable=False, default="system")
    calculated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

    trade: Mapped[Trade] = relationship(back_populates="brokerage_results")
    rule: Mapped[BrokerageRule] = relationship(back_populates="brokerage_results")


class AuditLog(Base):
    __tablename__ = "brokerage_audit"

    audit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(60), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    old_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    new_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_id: Mapped[str] = mapped_column(String(120), nullable=False, default="system")
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)

