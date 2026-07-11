CREATE TABLE client_master (
    client_id       VARCHAR2(40) PRIMARY KEY,
    client_name     VARCHAR2(200) NOT NULL,
    client_type     VARCHAR2(40) NOT NULL,
    country         VARCHAR2(40) DEFAULT 'IN' NOT NULL,
    is_active       NUMBER(1) DEFAULT 1 NOT NULL,
    created_at      TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at      TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE TABLE product_master (
    product_id      VARCHAR2(40) PRIMARY KEY,
    product_code    VARCHAR2(40) NOT NULL UNIQUE,
    product_name    VARCHAR2(200) NOT NULL,
    asset_class     VARCHAR2(80) NOT NULL,
    is_active       NUMBER(1) DEFAULT 1 NOT NULL,
    created_at      TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at      TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE SEQUENCE user_master_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE TABLE user_master (
    user_id        NUMBER PRIMARY KEY,
    username       VARCHAR2(80) NOT NULL UNIQUE,
    email          VARCHAR2(255) NOT NULL UNIQUE,
    full_name      VARCHAR2(200) NOT NULL,
    role           VARCHAR2(40) NOT NULL,
    password_hash  VARCHAR2(255) NOT NULL,
    is_active      NUMBER(1) DEFAULT 1 NOT NULL,
    created_at     TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at     TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE TABLE trade_master (
    trade_id         VARCHAR2(80) PRIMARY KEY,
    client_id        VARCHAR2(40) NOT NULL REFERENCES client_master(client_id),
    product_id       VARCHAR2(40) NOT NULL REFERENCES product_master(product_id),
    quantity         NUMBER(20, 4) NOT NULL,
    price            NUMBER(20, 6) NOT NULL,
    currency         VARCHAR2(3) NOT NULL,
    exchange         VARCHAR2(30) NOT NULL,
    trade_side       VARCHAR2(10) NOT NULL,
    trade_date       DATE NOT NULL,
    import_id        NUMBER,
    status           VARCHAR2(30) DEFAULT 'PENDING' NOT NULL,
    rejection_reason CLOB,
    created_at       TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at       TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE SEQUENCE brokerage_rule_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE TABLE brokerage_rule_master (
    rule_id          NUMBER PRIMARY KEY,
    product_code     VARCHAR2(40) NOT NULL,
    client_type      VARCHAR2(40) NOT NULL,
    exchange         VARCHAR2(30) NOT NULL,
    country          VARCHAR2(40) DEFAULT 'IN' NOT NULL,
    currency         VARCHAR2(3) DEFAULT 'INR' NOT NULL,
    trade_side       VARCHAR2(10) DEFAULT 'ANY' NOT NULL,
    brokerage_type   VARCHAR2(20) NOT NULL,
    brokerage_value  NUMBER(20, 6) NOT NULL,
    effective_date   DATE NOT NULL,
    expiry_date      DATE,
    priority         NUMBER DEFAULT 100 NOT NULL,
    is_active        NUMBER(1) DEFAULT 1 NOT NULL,
    created_at       TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL,
    updated_at       TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE SEQUENCE brokerage_result_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE TABLE brokerage_result (
    result_id           NUMBER PRIMARY KEY,
    trade_id            VARCHAR2(80) NOT NULL REFERENCES trade_master(trade_id),
    rule_id             NUMBER NOT NULL REFERENCES brokerage_rule_master(rule_id),
    trade_value         NUMBER(20, 2) NOT NULL,
    brokerage           NUMBER(20, 2) NOT NULL,
    gst                 NUMBER(20, 2) NOT NULL,
    stt                 NUMBER(20, 2) NOT NULL,
    exchange_txn_charge NUMBER(20, 2) NOT NULL,
    sebi_charge         NUMBER(20, 2) NOT NULL,
    total_charges       NUMBER(20, 2) NOT NULL,
    calculated_by       VARCHAR2(120) DEFAULT 'system' NOT NULL,
    calculated_at       TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE SEQUENCE brokerage_audit_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE TABLE brokerage_audit (
    audit_id       NUMBER PRIMARY KEY,
    entity_type    VARCHAR2(60) NOT NULL,
    entity_id      VARCHAR2(100) NOT NULL,
    action         VARCHAR2(60) NOT NULL,
    old_value      CLOB,
    new_value      CLOB,
    user_id        VARCHAR2(120) DEFAULT 'system' NOT NULL,
    change_reason  CLOB,
    created_at     TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX ix_trade_date ON trade_master(trade_date);
CREATE INDEX ix_trade_client ON trade_master(client_id);
CREATE INDEX ix_trade_product ON trade_master(product_id);
CREATE INDEX ix_trade_import ON trade_master(import_id);
CREATE INDEX ix_user_username ON user_master(username);
CREATE INDEX ix_user_role ON user_master(role);

CREATE SEQUENCE trade_import_batch_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE TABLE trade_import_batch (
    import_id      NUMBER PRIMARY KEY,
    filename       VARCHAR2(255) NOT NULL,
    source_type    VARCHAR2(20) NOT NULL,
    status         VARCHAR2(30) DEFAULT 'PROCESSING' NOT NULL,
    total_rows     NUMBER DEFAULT 0 NOT NULL,
    accepted_rows  NUMBER DEFAULT 0 NOT NULL,
    rejected_rows  NUMBER DEFAULT 0 NOT NULL,
    imported_by    VARCHAR2(120) DEFAULT 'api' NOT NULL,
    created_at     TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE SEQUENCE trade_import_reject_seq START WITH 1 INCREMENT BY 1 NOCACHE;

CREATE TABLE trade_import_reject (
    rejection_id  NUMBER PRIMARY KEY,
    import_id     NUMBER NOT NULL REFERENCES trade_import_batch(import_id),
    row_number    NUMBER NOT NULL,
    trade_id      VARCHAR2(80),
    reason        CLOB NOT NULL,
    raw_payload   CLOB NOT NULL,
    created_at    TIMESTAMP DEFAULT SYSTIMESTAMP NOT NULL
);

CREATE INDEX ix_import_reject_batch ON trade_import_reject(import_id);
CREATE INDEX ix_import_reject_trade ON trade_import_reject(trade_id);

ALTER TABLE trade_master ADD CONSTRAINT fk_trade_import_batch
    FOREIGN KEY (import_id) REFERENCES trade_import_batch(import_id);

CREATE INDEX ix_rule_lookup ON brokerage_rule_master(
    product_code,
    client_type,
    exchange,
    country,
    currency,
    trade_side,
    effective_date,
    expiry_date,
    is_active
);
CREATE INDEX ix_result_trade ON brokerage_result(trade_id);
CREATE INDEX ix_audit_entity ON brokerage_audit(entity_type, entity_id);
