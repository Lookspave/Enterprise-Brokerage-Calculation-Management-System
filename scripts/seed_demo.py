from datetime import date
from decimal import Decimal

from ebcms.core.enums import BrokerageType, TradeSide, TradeStatus
from ebcms.database import SessionLocal, init_db
from ebcms.models import BrokerageRule, Client, Product, Trade


def main() -> None:
    init_db()
    with SessionLocal() as db:
        if not db.get(Client, "C-DEMO-001"):
            db.add(
                Client(
                    client_id="C-DEMO-001",
                    client_name="Demo Retail Client",
                    client_type="RETAIL",
                    country="IN",
                )
            )

        if not db.get(Product, "P-EQ"):
            db.add(
                Product(
                    product_id="P-EQ",
                    product_code="EQUITY",
                    product_name="Cash Equity",
                    asset_class="EQUITY",
                )
            )

        if not db.get(Trade, "T-DEMO-001"):
            db.add(
                Trade(
                    trade_id="T-DEMO-001",
                    client_id="C-DEMO-001",
                    product_id="P-EQ",
                    quantity=Decimal("100"),
                    price=Decimal("250.00"),
                    currency="INR",
                    exchange="NSE",
                    trade_side=TradeSide.BUY.value,
                    trade_date=date.today(),
                    status=TradeStatus.VALIDATED.value,
                )
            )

        if not db.query(BrokerageRule).filter_by(product_code="EQUITY", client_type="RETAIL").first():
            db.add(
                BrokerageRule(
                    product_code="EQUITY",
                    client_type="RETAIL",
                    exchange="NSE",
                    country="IN",
                    currency="INR",
                    trade_side="ANY",
                    brokerage_type=BrokerageType.PERCENTAGE.value,
                    brokerage_value=Decimal("0.25"),
                    effective_date=date(2024, 1, 1),
                    priority=100,
                )
            )

        db.commit()

    print("Demo data seeded. Try POST /calculate with trade_id T-DEMO-001.")


if __name__ == "__main__":
    main()

