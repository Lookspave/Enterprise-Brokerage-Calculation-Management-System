import sys
import unittest
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ebcms.services.validation import validate_trade_record  # noqa: E402


class ValidationTests(unittest.TestCase):
    def test_valid_trade_passes(self) -> None:
        result = validate_trade_record(
            trade_id="T1",
            client_exists=True,
            product_exists=True,
            duplicate_trade_id=False,
            quantity=Decimal("10"),
            price=Decimal("100"),
            currency="INR",
            trade_side="BUY",
            trade_date=date.today(),
            allowed_currencies={"INR", "USD"},
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.issues, [])

    def test_invalid_trade_collects_all_issues(self) -> None:
        result = validate_trade_record(
            trade_id=" ",
            client_exists=False,
            product_exists=False,
            duplicate_trade_id=True,
            quantity=Decimal("0"),
            price=Decimal("-1"),
            currency="ABC",
            trade_side="HOLD",
            trade_date=date.today() + timedelta(days=1),
            allowed_currencies={"INR", "USD"},
        )

        self.assertFalse(result.is_valid)
        self.assertIn("Duplicate trade ID.", result.issues)
        self.assertIn("Invalid client.", result.issues)
        self.assertIn("Invalid product.", result.issues)
        self.assertIn("Invalid currency.", result.issues)
        self.assertIn("Invalid trade side.", result.issues)
        self.assertIn("Trade date cannot be in the future.", result.issues)


if __name__ == "__main__":
    unittest.main()

