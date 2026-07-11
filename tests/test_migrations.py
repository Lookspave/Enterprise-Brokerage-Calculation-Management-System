import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import create_engine, inspect  # noqa: E402

from ebcms.config import get_settings  # noqa: E402


class MigrationTests(unittest.TestCase):
    def test_initial_migration_creates_current_schema(self) -> None:
        project_root = Path(__file__).resolve().parents[1]
        original_database_url = os.environ.get("EBCMS_DATABASE_URL")

        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "migration-smoke.db"
            os.environ["EBCMS_DATABASE_URL"] = f"sqlite:///{database_path.as_posix()}"
            get_settings.cache_clear()

            try:
                config = Config(str(project_root / "alembic.ini"))
                command.upgrade(config, "head")

                engine = create_engine(os.environ["EBCMS_DATABASE_URL"])
                try:
                    tables = set(inspect(engine).get_table_names())
                finally:
                    engine.dispose()
            finally:
                if original_database_url is None:
                    os.environ.pop("EBCMS_DATABASE_URL", None)
                else:
                    os.environ["EBCMS_DATABASE_URL"] = original_database_url
                get_settings.cache_clear()

        self.assertTrue(
            {
                "alembic_version",
                "user_master",
                "client_master",
                "product_master",
                "trade_master",
                "trade_import_batch",
                "trade_import_reject",
                "brokerage_rule_master",
                "brokerage_result",
                "brokerage_audit",
            }.issubset(tables)
        )


if __name__ == "__main__":
    unittest.main()

