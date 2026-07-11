# EBCMS Oracle APEX Page Blueprint

## Application Shell

- Application name: Enterprise Brokerage Calculation & Management System
- Theme: Universal Theme
- Authentication: APEX accounts for demo, or custom auth mapped to `USER_MASTER.USERNAME`
- Authorization: use snippets in `security_authorization.sql`
- Global navigation: Dashboard, Trades, Imports, Rules, Revenue, Audit, Admin

## Page 1: Operations Dashboard

Purpose: first screen for operations and finance users.

Authorization: `CAN_VIEW_REPORTS`

Page items:

- `P1_BUSINESS_DATE`: Date picker, default `TRUNC(SYSDATE)`, LOV from `VW_DASHBOARD_SUMMARY`

Regions:

- KPI Cards: source `VW_DASHBOARD_SUMMARY`
  - Total Trades
  - Calculated Trades
  - Rejected Trades
  - Total Charges
  - Imports Count
  - Rejected Import Rows
- Daily Brokerage Trend: line chart using `VW_DAILY_BROKERAGE`
- Product Revenue: bar chart using `VW_PRODUCT_REVENUE`
- Exchange Revenue Share: pie or donut chart using `VW_EXCHANGE_REVENUE`
- Recent Audit: classic report on `BROKERAGE_AUDIT`, limited to latest rows

## Page 10: Trade Search

Purpose: operational trade review and reconciliation.

Authorization: authenticated users with trade read access.

Page items:

- `P10_DATE_FROM`
- `P10_DATE_TO`
- `P10_CLIENT_ID`
- `P10_PRODUCT_ID`
- `P10_EXCHANGE`
- `P10_STATUS`

Regions:

- Interactive Report: source `TRADE_MASTER` joined to `CLIENT_MASTER` and `PRODUCT_MASTER`
- Row details drawer or modal: trade details, latest brokerage result, rejection reason

Recommended actions:

- Link calculated trades to Page 40 brokerage result detail
- Link rejected trades to Page 50 rejection analysis

## Page 20: Import Monitoring

Purpose: monitor file loads and rejected records.

Authorization: `CAN_IMPORT_TRADES` for operational actions, `CAN_VIEW_REPORTS` for read-only access.

Regions:

- Import Batch Interactive Report: source `VW_IMPORT_BATCH_STATUS`
- Rejection Detail Interactive Report: source `VW_IMPORT_REJECTIONS`
- Rejection Rate Chart: `REJECTION_PCT` by import batch

Suggested filters:

- Import date range
- Imported by
- Source type
- Status

## Page 30: Brokerage Rules

Purpose: business-user rule management.

Authorization: `CAN_MANAGE_RULES`

Regions:

- Interactive Grid: source `BROKERAGE_RULE_MASTER`
- Rule Audit Report: source `BROKERAGE_AUDIT` filtered to `ENTITY_TYPE = 'BROKERAGE_RULE'`

Validation notes:

- `EFFECTIVE_DATE` must be before `EXPIRY_DATE` when expiry exists
- `BROKERAGE_TYPE` should be `PERCENTAGE` or `FLAT`
- `BROKERAGE_VALUE` must be positive

## Page 40: Revenue Analysis

Purpose: finance and management reporting.

Authorization: `CAN_VIEW_REPORTS`

Regions:

- Daily Brokerage: chart and interactive report from `VW_DAILY_BROKERAGE`
- Client Revenue: chart and report from `VW_CLIENT_REVENUE`
- Product Revenue: chart and report from `VW_PRODUCT_REVENUE`
- Exchange Revenue: chart and report from `VW_EXCHANGE_REVENUE`

Suggested filters:

- Date range
- Client type
- Product code
- Exchange
- Currency

## Page 50: Rejections And Exceptions

Purpose: triage bad trades and import failures.

Authorization: `CAN_IMPORT_TRADES`, `CAN_VIEW_REPORTS`, or `CAN_VIEW_AUDIT` depending on deployment policy.

Regions:

- Rejected Trades: source `VW_REJECTED_TRADES`
- Import Rejections: source `VW_IMPORT_REJECTIONS`
- Rejection Reasons: aggregate by reason, source `VW_IMPORT_REJECTIONS`

Recommended actions:

- Export rejected rows to CSV
- Link import rejection back to import batch
- Add remediation status later if workflow tracking is needed

## Page 60: Audit Trail

Purpose: compliance and risk audit review.

Authorization: `CAN_VIEW_AUDIT`

Regions:

- Audit Interactive Report: source `BROKERAGE_AUDIT`

Suggested filters:

- Entity type
- Entity ID
- Action
- User
- Date range

## Page 70: Admin

Purpose: user and role visibility for administrators.

Authorization: `IS_ADMIN`

Regions:

- Users Interactive Report: source `USER_MASTER`
- Active Reference Counts: source `VW_DASHBOARD_SUMMARY`

Security note:

- Do not expose `PASSWORD_HASH` in reports or forms.
- User creation and password changes should stay in the FastAPI backend unless a dedicated APEX password workflow is implemented.

