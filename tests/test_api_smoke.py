import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

_temp_dir = tempfile.TemporaryDirectory()
os.environ["EBCMS_DATABASE_URL"] = f"sqlite:///{Path(_temp_dir.name) / 'smoke.db'}"

from fastapi.testclient import TestClient  # noqa: E402

from ebcms.database import engine  # noqa: E402
from ebcms.main import app  # noqa: E402


def tearDownModule() -> None:
    engine.dispose()
    _temp_dir.cleanup()


class ApiSmokeTests(unittest.TestCase):
    def test_reference_trade_calculation_and_report_flow(self) -> None:
        with TestClient(app) as client:
            self.assertEqual(client.get("/health").json(), {"status": "ok"})
            self.assertEqual(client.get("/reports").status_code, 401)

            login_response = client.post(
                "/auth/login",
                data={"username": "admin", "password": "admin123"},
            )
            self.assertEqual(login_response.status_code, 200)
            admin_headers = {
                "Authorization": f"Bearer {login_response.json()['access_token']}",
            }
            me_response = client.get("/auth/me", headers=admin_headers)
            self.assertEqual(me_response.status_code, 200)
            self.assertEqual(me_response.json()["role"], "ADMIN")

            finance_user_response = client.post(
                "/users",
                headers=admin_headers,
                json={
                    "username": "finance1",
                    "email": "finance1@example.com",
                    "full_name": "Finance One",
                    "role": "FINANCE",
                    "password": "finance123",
                },
            )
            self.assertEqual(finance_user_response.status_code, 201)

            finance_login = client.post(
                "/auth/login",
                data={"username": "finance1", "password": "finance123"},
            )
            finance_headers = {
                "Authorization": f"Bearer {finance_login.json()['access_token']}",
            }
            forbidden_rule_response = client.post(
                "/rules",
                headers=finance_headers,
                json={
                    "product_code": "EQUITY",
                    "client_type": "RETAIL",
                    "exchange": "NSE",
                    "country": "IN",
                    "currency": "INR",
                    "trade_side": "ANY",
                    "brokerage_type": "PERCENTAGE",
                    "brokerage_value": "0.25",
                    "effective_date": "2026-01-01",
                    "priority": 100,
                },
            )
            self.assertEqual(forbidden_rule_response.status_code, 403)

            client_payload = {
                "client_id": "C-SMOKE-001",
                "client_name": "Smoke Test Retail Client",
                "client_type": "RETAIL",
                "country": "IN",
            }
            self.assertEqual(
                client.post("/client", headers=admin_headers, json=client_payload).status_code,
                201,
            )

            product_payload = {
                "product_id": "P-SMOKE-EQ",
                "product_code": "EQUITY",
                "product_name": "Cash Equity",
                "asset_class": "EQUITY",
            }
            self.assertEqual(
                client.post("/product", headers=admin_headers, json=product_payload).status_code,
                201,
            )

            rule_payload = {
                "product_code": "EQUITY",
                "client_type": "RETAIL",
                "exchange": "NSE",
                "country": "IN",
                "currency": "INR",
                "trade_side": "ANY",
                "brokerage_type": "PERCENTAGE",
                "brokerage_value": "0.25",
                "effective_date": "2026-01-01",
                "priority": 100,
            }
            rule_response = client.post("/rules", headers=admin_headers, json=rule_payload)
            self.assertEqual(rule_response.status_code, 201)
            self.assertEqual(rule_response.json()["brokerage_type"], "PERCENTAGE")

            trade_payload = {
                "trade_id": "T-SMOKE-001",
                "client_id": "C-SMOKE-001",
                "product_id": "P-SMOKE-EQ",
                "quantity": "100",
                "price": "250.00",
                "currency": "INR",
                "exchange": "NSE",
                "trade_side": "BUY",
                "trade_date": "2026-07-11",
            }
            trade_response = client.post("/trade", headers=admin_headers, json=trade_payload)
            self.assertEqual(trade_response.status_code, 201)
            self.assertEqual(trade_response.json()["status"], "VALIDATED")

            calculate_response = client.post(
                "/calculate",
                headers=admin_headers,
                json={"trade_id": "T-SMOKE-001", "calculated_by": "smoke-test"},
            )
            self.assertEqual(calculate_response.status_code, 200)
            calculation = calculate_response.json()
            self.assertEqual(calculation["trade_value"], "25000.00")
            self.assertEqual(calculation["brokerage"], "62.50")
            self.assertEqual(calculation["total_charges"], "80.84")

            brokerage_response = client.get("/brokerage/T-SMOKE-001", headers=admin_headers)
            self.assertEqual(brokerage_response.status_code, 200)
            self.assertEqual(brokerage_response.json()["total_charges"], "80.84")

            report_response = client.get("/reports", headers=finance_headers)
            self.assertEqual(report_response.status_code, 200)
            report = report_response.json()
            self.assertEqual(report["trade_count"], 1)
            self.assertEqual(report["total_charges"], "80.84")

            csv_content = "\n".join(
                [
                    "trade_id,client_id,product_id,quantity,price,currency,exchange,trade_side,trade_date",
                    "T-SMOKE-IMPORT-001,C-SMOKE-001,P-SMOKE-EQ,25,100.00,INR,NSE,BUY,2026-07-11",
                    "T-SMOKE-IMPORT-NORULE,C-SMOKE-001,P-SMOKE-EQ,10,100.00,INR,BSE,BUY,2026-07-11",
                    "T-SMOKE-IMPORT-002,C-SMOKE-001,P-MISSING,25,100.00,INR,NSE,BUY,2026-07-11",
                ]
            )
            import_response = client.post(
                "/trades/import",
                headers=admin_headers,
                data={"imported_by": "smoke-test"},
                files={"file": ("trades.csv", csv_content, "text/csv")},
            )
            self.assertEqual(import_response.status_code, 201)
            import_summary = import_response.json()
            self.assertEqual(import_summary["total_rows"], 3)
            self.assertEqual(import_summary["accepted_rows"], 2)
            self.assertEqual(import_summary["rejected_rows"], 1)
            self.assertEqual(
                import_summary["imported_trade_ids"],
                ["T-SMOKE-IMPORT-001", "T-SMOKE-IMPORT-NORULE"],
            )
            self.assertIn("Invalid product.", import_summary["rejected_records"][0]["reason"])

            imported_trade_response = client.get("/trade/T-SMOKE-IMPORT-001", headers=admin_headers)
            self.assertEqual(imported_trade_response.status_code, 200)
            self.assertEqual(imported_trade_response.json()["status"], "VALIDATED")

            rejection_response = client.get(
                f"/trades/imports/{import_summary['import_id']}/rejections",
                headers=admin_headers,
            )
            self.assertEqual(rejection_response.status_code, 200)
            rejections = rejection_response.json()
            self.assertEqual(len(rejections), 1)
            self.assertEqual(rejections[0]["trade_id"], "T-SMOKE-IMPORT-002")
            self.assertIn("Invalid product.", rejections[0]["reason"])

            batch_response = client.post(
                "/calculations/batch",
                headers=admin_headers,
                json={"import_id": import_summary["import_id"], "calculated_by": "batch-smoke"},
            )
            self.assertEqual(batch_response.status_code, 200)
            batch_summary = batch_response.json()
            self.assertEqual(batch_summary["total_trades"], 2)
            self.assertEqual(batch_summary["calculated_count"], 1)
            self.assertEqual(batch_summary["failed_count"], 1)
            self.assertEqual(batch_summary["total_brokerage"], "6.25")
            self.assertEqual(batch_summary["total_charges"], "8.09")
            self.assertEqual(batch_summary["calculated_trade_ids"], ["T-SMOKE-IMPORT-001"])
            self.assertEqual(batch_summary["failures"][0]["trade_id"], "T-SMOKE-IMPORT-NORULE")
            self.assertIn("No brokerage rule matched", batch_summary["failures"][0]["reason"])

            calculated_import_response = client.get(
                "/trade/T-SMOKE-IMPORT-001",
                headers=admin_headers,
            )
            self.assertEqual(calculated_import_response.status_code, 200)
            self.assertEqual(calculated_import_response.json()["status"], "CALCULATED")

            failed_import_response = client.get(
                "/trade/T-SMOKE-IMPORT-NORULE",
                headers=admin_headers,
            )
            self.assertEqual(failed_import_response.status_code, 200)
            self.assertEqual(failed_import_response.json()["status"], "VALIDATED")

            forbidden_audit_response = client.get("/audit", headers=finance_headers)
            self.assertEqual(forbidden_audit_response.status_code, 403)

            audit_response = client.get(
                "/audit?entity_type=BROKERAGE_RESULT&limit=10",
                headers=admin_headers,
            )
            self.assertEqual(audit_response.status_code, 200)
            audit_page = audit_response.json()
            self.assertEqual(audit_page["total"], 2)
            self.assertEqual(audit_page["items"][0]["entity_type"], "BROKERAGE_RESULT")
            self.assertEqual(audit_page["items"][0]["action"], "CALCULATE")

            dashboard_response = client.get(
                "/dashboard?business_date=2026-07-11",
                headers=finance_headers,
            )
            self.assertEqual(dashboard_response.status_code, 200)
            dashboard = dashboard_response.json()
            self.assertEqual(dashboard["today_trades"], 3)
            self.assertEqual(dashboard["today_brokerage"], "88.93")
            self.assertEqual(dashboard["pending_trades"], 0)
            self.assertEqual(dashboard["validated_trades"], 1)
            self.assertEqual(dashboard["calculated_trades"], 2)
            self.assertEqual(dashboard["rejected_trades"], 0)
            self.assertEqual(dashboard["imports_today"], 1)
            self.assertEqual(dashboard["rejected_import_rows_today"], 1)
            self.assertEqual(dashboard["active_rules"], 1)
            self.assertEqual(dashboard["active_clients"], 1)
            self.assertEqual(dashboard["active_products"], 1)
            self.assertGreaterEqual(len(dashboard["recent_audit"]), 1)


if __name__ == "__main__":
    unittest.main()
