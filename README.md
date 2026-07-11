# Enterprise Brokerage Calculation & Management System

A production-oriented portfolio scaffold for brokerage calculation, rule management, batch processing, audit, and reporting.

## What Is Included

- FastAPI backend with trade, rule, brokerage, client, product, and report endpoints.
- JWT-style bearer authentication with role-based access controls.
- CSV/XLSX trade import with row-level validation and rejected-record reporting.
- A pure Python brokerage engine with deterministic Decimal-based calculations.
- Validation services for duplicate, reference, currency, date, quantity, and price checks.
- SQLAlchemy models that run locally on SQLite and can point to Oracle with an Oracle SQLAlchemy URL.
- Oracle DDL and PL/SQL examples for production-style database design.
- PySpark batch job skeleton for high-volume trade processing.
- Airflow DAG skeleton for daily load, validate, calculate, report, and notify orchestration.
- Docker and environment templates.
- Focused unit tests for the core brokerage engine and validation layer.

## Quick Start

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python scripts/seed_demo.py
uvicorn ebcms.main:app --reload
```

Swagger UI will be available at:

```text
http://127.0.0.1:8000/docs
```

## Main API Endpoints

```text
POST /auth/login
GET  /auth/me
POST /users
POST /client
GET  /client/{client_id}
POST /product
GET  /product/{product_id}
POST /trade
POST /trades/import
GET  /trades/imports/{import_id}/rejections
GET  /trade/{trade_id}
POST /calculate
POST /calculations/batch
GET  /brokerage/{trade_id}
POST /rules
PUT  /rules/{rule_id}
DELETE /rules/{rule_id}
GET  /reports
GET  /audit
GET  /dashboard
```

## Local Demo Flow

After running `python scripts/seed_demo.py`, log in and use the token for protected endpoints.

Default local development admin:

```text
username: admin
password: admin123
```

PowerShell login helper:

```powershell
$token = (Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8000/auth/login `
  -ContentType "application/x-www-form-urlencoded" `
  -Body "username=admin&password=admin123").access_token
```

Then calculate the seeded trade:

```powershell
curl -X POST http://127.0.0.1:8000/calculate `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d "{\"trade_id\":\"T-DEMO-001\",\"calculated_by\":\"demo\"}"
```

Then fetch the result:

```powershell
curl http://127.0.0.1:8000/brokerage/T-DEMO-001 `
  -H "Authorization: Bearer $token"
```

## Roles

Supported roles:

```text
ADMIN
OPERATIONS
BROKERAGE_MANAGER
FINANCE
RISK
COMPLIANCE
RELATIONSHIP_MANAGER
```

Typical permissions:

- `ADMIN`: all operations, including user creation.
- `OPERATIONS`: create reference data, create/import trades, run calculations.
- `BROKERAGE_MANAGER`: manage brokerage rules and run calculations.
- `FINANCE`, `RISK`, `COMPLIANCE`: read reporting and selected reference/rule data.
- `RELATIONSHIP_MANAGER`: read selected client, product, and trade data.

## Import Trades

Upload a CSV or XLSX file with these columns:

```text
trade_id,client_id,product_id,quantity,price,currency,exchange,trade_side,trade_date
```

CSV example:

```powershell
curl -X POST http://127.0.0.1:8000/trades/import `
  -H "Authorization: Bearer $token" `
  -F "imported_by=demo" `
  -F "file=@data/sample_trades.csv"
```

The response includes accepted trade IDs and rejected rows with reasons. Persisted rejections can be fetched with:

```powershell
curl http://127.0.0.1:8000/trades/imports/1/rejections `
  -H "Authorization: Bearer $token"
```

## Batch Calculate Trades

Calculate all validated trades from an import batch:

```powershell
curl -X POST http://127.0.0.1:8000/calculations/batch `
  -H "Authorization: Bearer $token" `
  -H "Content-Type: application/json" `
  -d "{\"import_id\":1,\"calculated_by\":\"batch-demo\"}"
```

You can also calculate by date range or all currently validated trades:

```json
{
  "date_from": "2026-07-01",
  "date_to": "2026-07-31",
  "calculated_by": "batch-demo"
}
```

## Operations Dashboard And Audit

Dashboard summary:

```powershell
curl http://127.0.0.1:8000/dashboard?business_date=2026-07-11 `
  -H "Authorization: Bearer $token"
```

The dashboard includes trade counts, brokerage totals, import status, rejected import rows, active rules/reference data, and recent audit entries.

Audit trail:

```powershell
curl "http://127.0.0.1:8000/audit?entity_type=BROKERAGE_RESULT&limit=25" `
  -H "Authorization: Bearer $token"
```

Audit filters include `entity_type`, `entity_id`, `action`, `user_id`, `date_from`, `date_to`, `limit`, and `offset`.

## Oracle Configuration

The default development database is SQLite:

```text
sqlite:///./ebcms.db
```

For Oracle, set `EBCMS_DATABASE_URL`:

```text
oracle+oracledb://user:password@host:1521/?service_name=FREEPDB1
```

The production-oriented DDL lives in `sql/oracle_schema.sql`.

## Tests

```powershell
python -m unittest discover
```

For a broader project check:

```powershell
python -m compileall src tests scripts etl dags
```
