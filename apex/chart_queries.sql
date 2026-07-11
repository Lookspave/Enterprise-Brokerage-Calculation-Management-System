PROMPT EBCMS APEX chart query catalog

-- Dashboard KPI cards
SELECT
    total_trades,
    calculated_trades,
    rejected_trades,
    total_charges,
    imports_count,
    rejected_import_rows
FROM vw_dashboard_summary
WHERE business_date = NVL(:P1_BUSINESS_DATE, TRUNC(SYSDATE));

-- Line chart: daily total charges
SELECT
    business_date AS label,
    total_charges AS value
FROM vw_daily_brokerage
WHERE business_date BETWEEN NVL(:P1_DATE_FROM, business_date)
    AND NVL(:P1_DATE_TO, business_date)
ORDER BY business_date;

-- Bar chart: product revenue
SELECT
    product_code AS label,
    total_charges AS value
FROM vw_product_revenue
ORDER BY total_charges DESC;

-- Bar chart: client revenue
SELECT
    client_name AS label,
    total_charges AS value
FROM vw_client_revenue
ORDER BY total_charges DESC
FETCH FIRST 20 ROWS ONLY;

-- Pie chart: exchange revenue share
SELECT
    exchange AS label,
    total_charges AS value
FROM vw_exchange_revenue
ORDER BY total_charges DESC;

-- Interactive report: rejected import rows
SELECT
    import_id,
    filename,
    row_number,
    trade_id,
    reason,
    created_at
FROM vw_import_rejections
ORDER BY created_at DESC, import_id DESC, row_number;

-- Interactive report: audit trail
SELECT
    audit_id,
    entity_type,
    entity_id,
    action,
    user_id,
    change_reason,
    created_at
FROM brokerage_audit
ORDER BY created_at DESC, audit_id DESC;

