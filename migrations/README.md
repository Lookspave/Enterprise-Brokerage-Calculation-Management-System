# Database Migrations

This folder contains Alembic migrations for EBCMS.

Use the same database URL as the app:

```powershell
$env:EBCMS_DATABASE_URL = "sqlite:///./ebcms.db"
python scripts/migrate_db.py
```

For Oracle:

```text
oracle+oracledb://user:password@host:1521/?service_name=FREEPDB1
```

