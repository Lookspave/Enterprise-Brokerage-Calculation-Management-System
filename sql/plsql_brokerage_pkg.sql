CREATE OR REPLACE PACKAGE brokerage_calc_pkg AS
    FUNCTION calculate_brokerage(
        p_trade_value      IN NUMBER,
        p_brokerage_type   IN VARCHAR2,
        p_brokerage_value  IN NUMBER
    ) RETURN NUMBER;
END brokerage_calc_pkg;
/

CREATE OR REPLACE PACKAGE BODY brokerage_calc_pkg AS
    FUNCTION calculate_brokerage(
        p_trade_value      IN NUMBER,
        p_brokerage_type   IN VARCHAR2,
        p_brokerage_value  IN NUMBER
    ) RETURN NUMBER IS
    BEGIN
        IF UPPER(p_brokerage_type) = 'PERCENTAGE' THEN
            RETURN ROUND(p_trade_value * (p_brokerage_value / 100), 2);
        ELSIF UPPER(p_brokerage_type) = 'FLAT' THEN
            RETURN ROUND(p_brokerage_value, 2);
        END IF;

        RAISE_APPLICATION_ERROR(-20001, 'Unsupported brokerage type: ' || p_brokerage_type);
    END calculate_brokerage;
END brokerage_calc_pkg;
/

