import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ebcms.services.brokerage_engine import (  # noqa: E402
    BrokerageEngine,
    CalculationRule,
    CalculationTrade,
    NoApplicableRuleError,
    TaxProfile,
)


class BrokerageEngineTests(unittest.TestCase):
    def test_percentage_rule_calculates_all_charges(self) -> None:
        engine = BrokerageEngine(
            TaxProfile(
                gst_rate=Decimal("0.18"),
                stt_rate=Decimal("0.00025"),
                exchange_txn_rate=Decimal("0.0000325"),
                sebi_rate=Decimal("0.000001"),
            )
        )
        trade = CalculationTrade(
            trade_id="T1",
            product_code="EQUITY",
            client_type="RETAIL",
            exchange="NSE",
            country="IN",
            currency="INR",
            trade_side="BUY",
            quantity=Decimal("100"),
            price=Decimal("250"),
            trade_date=date(2026, 7, 11),
        )
        rule = CalculationRule(
            rule_id=1,
            product_code="EQUITY",
            client_type="RETAIL",
            exchange="NSE",
            country="IN",
            currency="INR",
            trade_side="ANY",
            brokerage_type="PERCENTAGE",
            brokerage_value=Decimal("0.25"),
            effective_date=date(2026, 1, 1),
        )

        result = engine.calculate(trade, rule)

        self.assertEqual(result.trade_value, Decimal("25000.00"))
        self.assertEqual(result.brokerage, Decimal("62.50"))
        self.assertEqual(result.gst, Decimal("11.25"))
        self.assertEqual(result.stt, Decimal("6.25"))
        self.assertEqual(result.exchange_txn_charge, Decimal("0.81"))
        self.assertEqual(result.sebi_charge, Decimal("0.03"))
        self.assertEqual(result.total_charges, Decimal("80.84"))

    def test_specific_rule_wins_over_wildcard(self) -> None:
        engine = BrokerageEngine()
        trade = CalculationTrade(
            trade_id="T2",
            product_code="OPTIONS",
            client_type="RETAIL",
            exchange="NSE",
            country="IN",
            currency="INR",
            trade_side="SELL",
            quantity=Decimal("1"),
            price=Decimal("100"),
            trade_date=date(2026, 7, 11),
        )
        wildcard = CalculationRule(
            rule_id=1,
            product_code="OPTIONS",
            client_type="RETAIL",
            exchange="NSE",
            country="IN",
            currency="INR",
            trade_side="ANY",
            brokerage_type="FLAT",
            brokerage_value=Decimal("20"),
            effective_date=date(2026, 1, 1),
        )
        specific = CalculationRule(
            rule_id=2,
            product_code="OPTIONS",
            client_type="RETAIL",
            exchange="NSE",
            country="IN",
            currency="INR",
            trade_side="SELL",
            brokerage_type="FLAT",
            brokerage_value=Decimal("15"),
            effective_date=date(2026, 1, 1),
        )

        self.assertEqual(engine.find_applicable_rule(trade, [wildcard, specific]).rule_id, 2)

    def test_missing_rule_raises_clear_error(self) -> None:
        engine = BrokerageEngine()
        trade = CalculationTrade(
            trade_id="T3",
            product_code="FX",
            client_type="INSTITUTIONAL",
            exchange="OTC",
            country="IN",
            currency="USD",
            trade_side="BUY",
            quantity=Decimal("10"),
            price=Decimal("100"),
            trade_date=date(2026, 7, 11),
        )

        with self.assertRaises(NoApplicableRuleError):
            engine.find_applicable_rule(trade, [])


if __name__ == "__main__":
    unittest.main()

