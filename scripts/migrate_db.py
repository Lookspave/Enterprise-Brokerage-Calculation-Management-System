from pathlib import Path

from alembic import command
from alembic.config import Config


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    alembic_config = Config(str(project_root / "alembic.ini"))
    command.upgrade(alembic_config, "head")


if __name__ == "__main__":
    main()

