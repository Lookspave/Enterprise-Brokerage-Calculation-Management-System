import unittest
from pathlib import Path


class ApexAssetTests(unittest.TestCase):
    def test_required_reporting_views_are_defined(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        views_sql = (project_root / "apex" / "reporting_views.sql").read_text(encoding="utf-8")
        normalized = views_sql.lower()

        required_views = {
            "vw_dashboard_summary",
            "vw_daily_brokerage",
            "vw_client_revenue",
            "vw_product_revenue",
            "vw_exchange_revenue",
            "vw_rejected_trades",
            "vw_import_batch_status",
        }

        for view_name in required_views:
            self.assertIn(f"create or replace view {view_name}", normalized)

    def test_apex_blueprint_has_core_pages(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        blueprint = (project_root / "apex" / "page_blueprint.md").read_text(encoding="utf-8")

        for page_name in [
            "Operations Dashboard",
            "Trade Search",
            "Import Monitoring",
            "Brokerage Rules",
            "Revenue Analysis",
            "Rejections And Exceptions",
            "Audit Trail",
            "Admin",
        ]:
            self.assertIn(page_name, blueprint)

    def test_local_preview_page_exists(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        preview = (project_root / "apex" / "preview.html").read_text(encoding="utf-8")

        self.assertIn("EBCMS APEX Interactive Preview", preview)
        self.assertIn("Operations Dashboard", preview)
        self.assertIn("const previewData", preview)
        self.assertIn("function renderTrades", preview)
        self.assertIn("function renderAudit", preview)
        self.assertIn("data-page", preview)


if __name__ == "__main__":
    unittest.main()
