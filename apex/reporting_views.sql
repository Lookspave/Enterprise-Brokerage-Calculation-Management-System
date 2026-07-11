PROMPT Creating EBCMS APEX reporting views

CREATE OR REPLACE VIEW vw_daily_brokerage AS
SELECT
    TRUNC(t.trade_date) AS business_date,
    COUNT(*) AS calculated_trades,
    SUM(r.trade_value) AS trade_value,
    SUM(r.brokerage) AS total_brokerage,
    SUM(r.gst) AS total_gst,
    SUM(r.stt) AS total_stt,
    SUM(r.exchange_txn_charge) AS total_exchange_txn_charge,
    SUM(r.sebi_charge) AS total_sebi_charge,
    SUM(r.total_charges) AS total_charges
FROM brokerage_result r
JOIN trade_master t
    ON t.trade_id = r.trade_id
GROUP BY TRUNC(t.trade_date);

CREATE OR REPLACE VIEW vw_client_revenue AS
SELECT
    c.client_id,
    c.client_name,
    c.client_type,
    c.country,
    COUNT(r.result_id) AS calculated_trades,
    SUM(r.trade_value) AS trade_value,
    SUM(r.brokerage) AS total_brokerage,
    SUM(r.total_charges) AS total_charges,
    MIN(t.trade_date) AS first_trade_date,
    MAX(t.trade_date) AS last_trade_date
FROM brokerage_result r
JOIN trade_master t
    ON t.trade_id = r.trade_id
JOIN client_master c
    ON c.client_id = t.client_id
GROUP BY
    c.client_id,
    c.client_name,
    c.client_type,
    c.country;

CREATE OR REPLACE VIEW vw_product_revenue AS
SELECT
    p.product_id,
    p.product_code,
    p.product_name,
    p.asset_class,
    COUNT(r.result_id) AS calculated_trades,
    SUM(r.trade_value) AS trade_value,
    SUM(r.brokerage) AS total_brokerage,
    SUM(r.total_charges) AS total_charges,
    MIN(t.trade_date) AS first_trade_date,
    MAX(t.trade_date) AS last_trade_date
FROM brokerage_result r
JOIN trade_master t
    ON t.trade_id = r.trade_id
JOIN product_master p
    ON p.product_id = t.product_id
GROUP BY
    p.product_id,
    p.product_code,
    p.product_name,
    p.asset_class;

CREATE OR REPLACE VIEW vw_exchange_revenue AS
SELECT
    t.exchange,
    t.currency,
    COUNT(r.result_id) AS calculated_trades,
    SUM(r.trade_value) AS trade_value,
    SUM(r.brokerage) AS total_brokerage,
    SUM(r.total_charges) AS total_charges,
    MIN(t.trade_date) AS first_trade_date,
    MAX(t.trade_date) AS last_trade_date
FROM brokerage_result r
JOIN trade_master t
    ON t.trade_id = r.trade_id
GROUP BY
    t.exchange,
    t.currency;

CREATE OR REPLACE VIEW vw_rejected_trades AS
SELECT
    t.trade_id,
    t.client_id,
    c.client_name,
    t.product_id,
    p.product_code,
    t.exchange,
    t.currency,
    t.trade_side,
    t.quantity,
    t.price,
    t.trade_date,
    t.status,
    t.rejection_reason,
    t.created_at
FROM trade_master t
LEFT JOIN client_master c
    ON c.client_id = t.client_id
LEFT JOIN product_master p
    ON p.product_id = t.product_id
WHERE t.status = 'REJECTED';

CREATE OR REPLACE VIEW vw_import_batch_status AS
SELECT
    b.import_id,
    b.filename,
    b.source_type,
    b.status,
    b.total_rows,
    b.accepted_rows,
    b.rejected_rows,
    CASE
        WHEN b.total_rows = 0 THEN 0
        ELSE ROUND((b.rejected_rows / b.total_rows) * 100, 2)
    END AS rejection_pct,
    b.imported_by,
    b.created_at,
    COUNT(t.trade_id) AS persisted_trades,
    COUNT(r.rejection_id) AS persisted_rejections
FROM trade_import_batch b
LEFT JOIN trade_master t
    ON t.import_id = b.import_id
LEFT JOIN trade_import_reject r
    ON r.import_id = b.import_id
GROUP BY
    b.import_id,
    b.filename,
    b.source_type,
    b.status,
    b.total_rows,
    b.accepted_rows,
    b.rejected_rows,
    b.imported_by,
    b.created_at;

CREATE OR REPLACE VIEW vw_import_rejections AS
SELECT
    r.rejection_id,
    r.import_id,
    b.filename,
    r.row_number,
    r.trade_id,
    r.reason,
    r.raw_payload,
    r.created_at
FROM trade_import_reject r
JOIN trade_import_batch b
    ON b.import_id = r.import_id;

CREATE OR REPLACE VIEW vw_dashboard_summary AS
WITH reporting_dates AS (
    SELECT TRUNC(trade_date) AS business_date
    FROM trade_master
    UNION
    SELECT TRUNC(CAST(created_at AS DATE)) AS business_date
    FROM trade_import_batch
    UNION
    SELECT TRUNC(SYSDATE) AS business_date
    FROM dual
),
trade_counts AS (
    SELECT
        TRUNC(trade_date) AS business_date,
        COUNT(*) AS total_trades,
        SUM(CASE WHEN status = 'PENDING' THEN 1 ELSE 0 END) AS pending_trades,
        SUM(CASE WHEN status = 'VALIDATED' THEN 1 ELSE 0 END) AS validated_trades,
        SUM(CASE WHEN status = 'CALCULATED' THEN 1 ELSE 0 END) AS calculated_trades,
        SUM(CASE WHEN status = 'REJECTED' THEN 1 ELSE 0 END) AS rejected_trades
    FROM trade_master
    GROUP BY TRUNC(trade_date)
),
brokerage_totals AS (
    SELECT
        TRUNC(t.trade_date) AS business_date,
        COUNT(r.result_id) AS result_count,
        SUM(r.trade_value) AS trade_value,
        SUM(r.brokerage) AS total_brokerage,
        SUM(r.total_charges) AS total_charges
    FROM brokerage_result r
    JOIN trade_master t
        ON t.trade_id = r.trade_id
    GROUP BY TRUNC(t.trade_date)
),
import_totals AS (
    SELECT
        TRUNC(CAST(created_at AS DATE)) AS business_date,
        COUNT(*) AS imports_count,
        SUM(total_rows) AS imported_rows,
        SUM(accepted_rows) AS accepted_rows,
        SUM(rejected_rows) AS rejected_rows
    FROM trade_import_batch
    GROUP BY TRUNC(CAST(created_at AS DATE))
),
reference_counts AS (
    SELECT
        (SELECT COUNT(*) FROM client_master WHERE is_active = 1) AS active_clients,
        (SELECT COUNT(*) FROM product_master WHERE is_active = 1) AS active_products,
        (SELECT COUNT(*) FROM brokerage_rule_master WHERE is_active = 1) AS active_rules
    FROM dual
)
SELECT
    d.business_date,
    NVL(tc.total_trades, 0) AS total_trades,
    NVL(tc.pending_trades, 0) AS pending_trades,
    NVL(tc.validated_trades, 0) AS validated_trades,
    NVL(tc.calculated_trades, 0) AS calculated_trades,
    NVL(tc.rejected_trades, 0) AS rejected_trades,
    NVL(bt.result_count, 0) AS calculated_results,
    NVL(bt.trade_value, 0) AS trade_value,
    NVL(bt.total_brokerage, 0) AS total_brokerage,
    NVL(bt.total_charges, 0) AS total_charges,
    NVL(it.imports_count, 0) AS imports_count,
    NVL(it.imported_rows, 0) AS imported_rows,
    NVL(it.accepted_rows, 0) AS accepted_import_rows,
    NVL(it.rejected_rows, 0) AS rejected_import_rows,
    rc.active_clients,
    rc.active_products,
    rc.active_rules
FROM reporting_dates d
LEFT JOIN trade_counts tc
    ON tc.business_date = d.business_date
LEFT JOIN brokerage_totals bt
    ON bt.business_date = d.business_date
LEFT JOIN import_totals it
    ON it.business_date = d.business_date
CROSS JOIN reference_counts rc;

PROMPT APEX reporting views created

