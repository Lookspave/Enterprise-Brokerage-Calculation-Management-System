# Oracle APEX Dashboard Foundation

This folder contains APEX-ready supporting assets for the Enterprise Brokerage Calculation & Management System.

## Install Order

Run the core schema first:

```sql
@../sql/oracle_schema.sql
@../sql/plsql_brokerage_pkg.sql
```

Then install the reporting views:

```sql
@apex/reporting_views.sql
```

If you are using SQLcl or SQL*Plus from inside the `apex/` folder, you can also run:

```sql
@install_supporting_objects.sql
```

## Files

- `reporting_views.sql`: APEX-ready views for dashboard cards, charts, and reports.
- `chart_queries.sql`: Region source SQL for charts and interactive reports.
- `lov_queries.sql`: Shared LOV SQL for page filters and form items.
- `security_authorization.sql`: APEX authorization scheme snippets.
- `page_blueprint.md`: Page-by-page APEX build plan.

## Main Views

- `VW_DASHBOARD_SUMMARY`
- `VW_DAILY_BROKERAGE`
- `VW_CLIENT_REVENUE`
- `VW_PRODUCT_REVENUE`
- `VW_EXCHANGE_REVENUE`
- `VW_REJECTED_TRADES`
- `VW_IMPORT_BATCH_STATUS`
- `VW_IMPORT_REJECTIONS`

