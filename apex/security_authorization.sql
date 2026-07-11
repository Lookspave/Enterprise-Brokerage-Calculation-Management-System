PROMPT EBCMS APEX authorization SQL snippets

-- Use these snippets in APEX Authorization Schemes.
-- They assume APEX :APP_USER matches USER_MASTER.USERNAME.

-- Scheme: IS_ADMIN
RETURN EXISTS (
    SELECT 1
    FROM user_master
    WHERE UPPER(username) = UPPER(:APP_USER)
      AND is_active = 1
      AND role = 'ADMIN'
);

-- Scheme: CAN_MANAGE_RULES
RETURN EXISTS (
    SELECT 1
    FROM user_master
    WHERE UPPER(username) = UPPER(:APP_USER)
      AND is_active = 1
      AND role IN ('ADMIN', 'BROKERAGE_MANAGER')
);

-- Scheme: CAN_IMPORT_TRADES
RETURN EXISTS (
    SELECT 1
    FROM user_master
    WHERE UPPER(username) = UPPER(:APP_USER)
      AND is_active = 1
      AND role IN ('ADMIN', 'OPERATIONS')
);

-- Scheme: CAN_RUN_CALCULATIONS
RETURN EXISTS (
    SELECT 1
    FROM user_master
    WHERE UPPER(username) = UPPER(:APP_USER)
      AND is_active = 1
      AND role IN ('ADMIN', 'OPERATIONS', 'BROKERAGE_MANAGER')
);

-- Scheme: CAN_VIEW_REPORTS
RETURN EXISTS (
    SELECT 1
    FROM user_master
    WHERE UPPER(username) = UPPER(:APP_USER)
      AND is_active = 1
      AND role IN ('ADMIN', 'BROKERAGE_MANAGER', 'FINANCE', 'RISK', 'COMPLIANCE')
);

-- Scheme: CAN_VIEW_AUDIT
RETURN EXISTS (
    SELECT 1
    FROM user_master
    WHERE UPPER(username) = UPPER(:APP_USER)
      AND is_active = 1
      AND role IN ('ADMIN', 'RISK', 'COMPLIANCE')
);

