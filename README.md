# Enterprise Brokerage Calculation & Management System

A production-oriented portfolio scaffold for brokerage calculation, rule management, batch processing, audit, and reporting.

## What Is Included

- FastAPI backend with trade, rule, brokerage, client, product, and report endpoints.
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
POST /client
GET  /client/{client_id}
POST /product
GET  /product/{product_id}
POST /trade
GET  /trade/{trade_id}
POST /calculate
GET  /brokerage/{trade_id}
POST /rules
PUT  /rules/{rule_id}
DELETE /rules/{rule_id}
GET  /reports
```

## Local Demo Flow

After running `python scripts/seed_demo.py`, calculate the seeded trade:

```powershell
curl -X POST http://127.0.0.1:8000/calculate `
  -H "Content-Type: application/json" `
  -d "{\"trade_id\":\"T-DEMO-001\",\"calculated_by\":\"demo\"}"
```

Then fetch the result:

```powershell
curl http://127.0.0.1:8000/brokerage/T-DEMO-001
```

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

