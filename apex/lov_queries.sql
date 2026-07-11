PROMPT EBCMS APEX LOV query catalog

-- Business dates
SELECT TO_CHAR(business_date, 'YYYY-MM-DD') AS display_value,
       business_date AS return_value
FROM vw_dashboard_summary
ORDER BY business_date DESC;

-- Clients
SELECT client_name || ' (' || client_id || ')' AS display_value,
       client_id AS return_value
FROM client_master
WHERE is_active = 1
ORDER BY client_name;

-- Products
SELECT product_code || ' - ' || product_name AS display_value,
       product_id AS return_value
FROM product_master
WHERE is_active = 1
ORDER BY product_code;

-- Product codes for rules and charts
SELECT DISTINCT product_code AS display_value,
       product_code AS return_value
FROM product_master
ORDER BY product_code;

-- Exchanges
SELECT DISTINCT exchange AS display_value,
       exchange AS return_value
FROM trade_master
ORDER BY exchange;

-- Trade statuses
SELECT 'Pending' AS display_value, 'PENDING' AS return_value FROM dual
UNION ALL SELECT 'Validated', 'VALIDATED' FROM dual
UNION ALL SELECT 'Calculated', 'CALCULATED' FROM dual
UNION ALL SELECT 'Rejected', 'REJECTED' FROM dual;

-- User roles
SELECT 'Administrator' AS display_value, 'ADMIN' AS return_value FROM dual
UNION ALL SELECT 'Operations', 'OPERATIONS' FROM dual
UNION ALL SELECT 'Brokerage Manager', 'BROKERAGE_MANAGER' FROM dual
UNION ALL SELECT 'Finance', 'FINANCE' FROM dual
UNION ALL SELECT 'Risk', 'RISK' FROM dual
UNION ALL SELECT 'Compliance', 'COMPLIANCE' FROM dual
UNION ALL SELECT 'Relationship Manager', 'RELATIONSHIP_MANAGER' FROM dual;

