# Architecture

```text
CSV / Excel
    |
FastAPI upload or PySpark batch ingestion
    |
Validation layer
    |
Staging / trade tables
    |
Brokerage rule matching
    |
Brokerage, tax, and charge calculation
    |
Brokerage result + audit tables
    |
REST APIs, reports, dashboards, and downstream systems
```

## Core Boundaries

- `ebcms.services.brokerage_engine` contains pure calculation logic.
- `ebcms.services.validation` contains record-level validation rules.
- `ebcms.api.routes` exposes the operational API.
- `sql/` contains Oracle-oriented schema and PL/SQL examples.
- `etl/pyspark/` contains scalable batch calculation flow.
- `dags/` contains scheduler orchestration.

## Rule Matching

Rules match on product, client type, exchange, country, currency, trade side, and effective date range. `ANY`, `ALL`, `*`, and null are treated as wildcards. If multiple rules match, the engine chooses the most specific rule, then highest priority, then newest effective date.

