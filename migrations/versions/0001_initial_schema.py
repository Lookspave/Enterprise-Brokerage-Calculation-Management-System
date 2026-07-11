"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-11
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "client_master",
        sa.Column("client_id", sa.String(length=40), nullable=False),
        sa.Column("client_name", sa.String(length=200), nullable=False),
        sa.Column("client_type", sa.String(length=40), nullable=False),
        sa.Column("country", sa.String(length=40), nullable=False, server_default="IN"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("client_id"),
    )
    op.create_index("ix_client_master_client_type", "client_master", ["client_type"])

    op.create_table(
        "product_master",
        sa.Column("product_id", sa.String(length=40), nullable=False),
        sa.Column("product_code", sa.String(length=40), nullable=False),
        sa.Column("product_name", sa.String(length=200), nullable=False),
        sa.Column("asset_class", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("product_id"),
        sa.UniqueConstraint("product_code"),
    )

    op.create_table(
        "user_master",
        sa.Column("user_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=40), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_index("ix_user_master_role", "user_master", ["role"])
    op.create_index("ix_user_master_username", "user_master", ["username"])

    op.create_table(
        "trade_import_batch",
        sa.Column("import_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PROCESSING"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_by", sa.String(length=120), nullable=False, server_default="api"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("import_id"),
    )
    op.create_index("ix_trade_import_batch_created_at", "trade_import_batch", ["created_at"])

    op.create_table(
        "brokerage_rule_master",
        sa.Column("rule_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("product_code", sa.String(length=40), nullable=False),
        sa.Column("client_type", sa.String(length=40), nullable=False),
        sa.Column("exchange", sa.String(length=30), nullable=False),
        sa.Column("country", sa.String(length=40), nullable=False, server_default="IN"),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="INR"),
        sa.Column("trade_side", sa.String(length=10), nullable=False, server_default="ANY"),
        sa.Column("brokerage_type", sa.String(length=20), nullable=False),
        sa.Column("brokerage_value", sa.Numeric(20, 6), nullable=False),
        sa.Column("effective_date", sa.Date(), nullable=False),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("rule_id"),
    )
    op.create_index("ix_brokerage_rule_master_client_type", "brokerage_rule_master", ["client_type"])
    op.create_index("ix_brokerage_rule_master_exchange", "brokerage_rule_master", ["exchange"])
    op.create_index("ix_brokerage_rule_master_product_code", "brokerage_rule_master", ["product_code"])
    op.create_index(
        "ix_rule_lookup",
        "brokerage_rule_master",
        [
            "product_code",
            "client_type",
            "exchange",
            "country",
            "currency",
            "trade_side",
            "effective_date",
            "expiry_date",
            "is_active",
        ],
    )

    op.create_table(
        "trade_master",
        sa.Column("trade_id", sa.String(length=80), nullable=False),
        sa.Column("client_id", sa.String(length=40), nullable=False),
        sa.Column("product_id", sa.String(length=40), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 4), nullable=False),
        sa.Column("price", sa.Numeric(20, 6), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("exchange", sa.String(length=30), nullable=False),
        sa.Column("trade_side", sa.String(length=10), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("import_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["client_id"], ["client_master.client_id"]),
        sa.ForeignKeyConstraint(["import_id"], ["trade_import_batch.import_id"]),
        sa.ForeignKeyConstraint(["product_id"], ["product_master.product_id"]),
        sa.PrimaryKeyConstraint("trade_id"),
    )
    op.create_index("ix_trade_master_client_id", "trade_master", ["client_id"])
    op.create_index("ix_trade_master_currency", "trade_master", ["currency"])
    op.create_index("ix_trade_master_exchange", "trade_master", ["exchange"])
    op.create_index("ix_trade_master_import_id", "trade_master", ["import_id"])
    op.create_index("ix_trade_master_product_id", "trade_master", ["product_id"])
    op.create_index("ix_trade_master_trade_date", "trade_master", ["trade_date"])

    op.create_table(
        "trade_import_reject",
        sa.Column("rejection_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("import_id", sa.Integer(), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("trade_id", sa.String(length=80), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("raw_payload", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["import_id"], ["trade_import_batch.import_id"]),
        sa.PrimaryKeyConstraint("rejection_id"),
    )
    op.create_index("ix_trade_import_reject_created_at", "trade_import_reject", ["created_at"])
    op.create_index("ix_trade_import_reject_import_id", "trade_import_reject", ["import_id"])
    op.create_index("ix_trade_import_reject_trade_id", "trade_import_reject", ["trade_id"])

    op.create_table(
        "brokerage_result",
        sa.Column("result_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("trade_id", sa.String(length=80), nullable=False),
        sa.Column("rule_id", sa.Integer(), nullable=False),
        sa.Column("trade_value", sa.Numeric(20, 2), nullable=False),
        sa.Column("brokerage", sa.Numeric(20, 2), nullable=False),
        sa.Column("gst", sa.Numeric(20, 2), nullable=False),
        sa.Column("stt", sa.Numeric(20, 2), nullable=False),
        sa.Column("exchange_txn_charge", sa.Numeric(20, 2), nullable=False),
        sa.Column("sebi_charge", sa.Numeric(20, 2), nullable=False),
        sa.Column("total_charges", sa.Numeric(20, 2), nullable=False),
        sa.Column("calculated_by", sa.String(length=120), nullable=False, server_default="system"),
        sa.Column("calculated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["rule_id"], ["brokerage_rule_master.rule_id"]),
        sa.ForeignKeyConstraint(["trade_id"], ["trade_master.trade_id"]),
        sa.PrimaryKeyConstraint("result_id"),
    )
    op.create_index("ix_brokerage_result_calculated_at", "brokerage_result", ["calculated_at"])
    op.create_index("ix_brokerage_result_rule_id", "brokerage_result", ["rule_id"])
    op.create_index("ix_brokerage_result_trade_id", "brokerage_result", ["trade_id"])

    op.create_table(
        "brokerage_audit",
        sa.Column("audit_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("entity_type", sa.String(length=60), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=60), nullable=False),
        sa.Column("old_value", sa.Text(), nullable=True),
        sa.Column("new_value", sa.Text(), nullable=True),
        sa.Column("user_id", sa.String(length=120), nullable=False, server_default="system"),
        sa.Column("change_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("audit_id"),
    )
    op.create_index("ix_audit_entity", "brokerage_audit", ["entity_type", "entity_id"])
    op.create_index("ix_brokerage_audit_created_at", "brokerage_audit", ["created_at"])
    op.create_index("ix_brokerage_audit_entity_id", "brokerage_audit", ["entity_id"])
    op.create_index("ix_brokerage_audit_entity_type", "brokerage_audit", ["entity_type"])


def downgrade() -> None:
    op.drop_index("ix_brokerage_audit_entity_type", table_name="brokerage_audit")
    op.drop_index("ix_brokerage_audit_entity_id", table_name="brokerage_audit")
    op.drop_index("ix_brokerage_audit_created_at", table_name="brokerage_audit")
    op.drop_index("ix_audit_entity", table_name="brokerage_audit")
    op.drop_table("brokerage_audit")

    op.drop_index("ix_brokerage_result_trade_id", table_name="brokerage_result")
    op.drop_index("ix_brokerage_result_rule_id", table_name="brokerage_result")
    op.drop_index("ix_brokerage_result_calculated_at", table_name="brokerage_result")
    op.drop_table("brokerage_result")

    op.drop_index("ix_trade_import_reject_trade_id", table_name="trade_import_reject")
    op.drop_index("ix_trade_import_reject_import_id", table_name="trade_import_reject")
    op.drop_index("ix_trade_import_reject_created_at", table_name="trade_import_reject")
    op.drop_table("trade_import_reject")

    op.drop_index("ix_trade_master_trade_date", table_name="trade_master")
    op.drop_index("ix_trade_master_product_id", table_name="trade_master")
    op.drop_index("ix_trade_master_import_id", table_name="trade_master")
    op.drop_index("ix_trade_master_exchange", table_name="trade_master")
    op.drop_index("ix_trade_master_currency", table_name="trade_master")
    op.drop_index("ix_trade_master_client_id", table_name="trade_master")
    op.drop_table("trade_master")

    op.drop_index("ix_rule_lookup", table_name="brokerage_rule_master")
    op.drop_index("ix_brokerage_rule_master_product_code", table_name="brokerage_rule_master")
    op.drop_index("ix_brokerage_rule_master_exchange", table_name="brokerage_rule_master")
    op.drop_index("ix_brokerage_rule_master_client_type", table_name="brokerage_rule_master")
    op.drop_table("brokerage_rule_master")

    op.drop_index("ix_trade_import_batch_created_at", table_name="trade_import_batch")
    op.drop_table("trade_import_batch")

    op.drop_index("ix_user_master_username", table_name="user_master")
    op.drop_index("ix_user_master_role", table_name="user_master")
    op.drop_table("user_master")

    op.drop_table("product_master")

    op.drop_index("ix_client_master_client_type", table_name="client_master")
    op.drop_table("client_master")

