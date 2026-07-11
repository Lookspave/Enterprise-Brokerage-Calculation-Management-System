from datetime import date
from decimal import Decimal

from ebcms.core.enums import BrokerageType, TradeSide, TradeStatus, UserRole
from ebcms.database import SessionLocal, init_db
from ebcms.models import BrokerageRule, Client, Product, Trade, User
from ebcms.services.auth import hash_password


def main() -> None:
    init_db()
    with SessionLocal() as db:
        demo_users = [
            ("ops", "ops@example.com", "Operations User", UserRole.OPERATIONS.value, "ops12345"),
            (
                "brokerage",
                "brokerage@example.com",
                "Brokerage Manager",
                UserRole.BROKERAGE_MANAGER.value,
                "brokerage123",
            ),
            ("finance", "finance@example.com", "Finance User", UserRole.FINANCE.value, "finance123"),
        ]
        for username, email, full_name, role, password in demo_users:
            if not db.query(User).filter_by(username=username).first():
                db.add(
                    User(
                        username=username,
                        email=email,
                        full_name=full_name,
                        role=role,
                        password_hash=hash_password(password),
                    )
                )

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

    print("Demo data seeded.")
    print("Default login: admin / admin123")
    print("Demo users: ops / ops12345, brokerage / brokerage123, finance / finance123")
    print("Try POST /calculate with trade_id T-DEMO-001 using a bearer token.")


if __name__ == "__main__":
    main()
