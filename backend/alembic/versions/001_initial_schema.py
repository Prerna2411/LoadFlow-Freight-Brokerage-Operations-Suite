"""initial LoadFlow schema

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-07-14
"""

from alembic import op
import sqlalchemy as sa

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(160), nullable=False, unique=True),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(80), nullable=False, unique=True),
        sa.Column("description", sa.String(200), nullable=False),
    )
    op.create_table(
        "roles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.UniqueConstraint("organization_id", "name", name="uq_role_org_name"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(180), nullable=False, unique=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("account_type", sa.String(20), nullable=False),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_table("role_permissions", sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), primary_key=True), sa.Column("permission_id", sa.Integer(), sa.ForeignKey("permissions.id"), primary_key=True))
    op.create_table("user_roles", sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), primary_key=True), sa.Column("role_id", sa.Integer(), sa.ForeignKey("roles.id"), primary_key=True))
    op.create_table(
        "carrier_compliance",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("carrier_org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False, unique=True),
        sa.Column("insurance_expiry", sa.Date(), nullable=False),
        sa.Column("authority_status", sa.String(30), nullable=False),
        sa.Column("approved_equipment", sa.Text(), nullable=False),
        sa.Column("approved_commodities", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "rate_confirmation_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("load_id", sa.Integer(), nullable=False),
        sa.Column("carrier_org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("base_rate", sa.Float(), nullable=False),
        sa.Column("accessorials", sa.Text(), nullable=False),
        sa.Column("confirmed_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("load_id", "version", name="uq_load_rate_version"),
    )
    op.create_table(
        "loads",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("reference", sa.String(40), nullable=False, unique=True),
        sa.Column("broker_org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("shipper_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("carrier_org_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("origin", sa.String(160), nullable=False),
        sa.Column("destination", sa.String(160), nullable=False),
        sa.Column("equipment_type", sa.String(80), nullable=False),
        sa.Column("commodity", sa.String(100), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("compliance_flag", sa.Boolean(), nullable=False),
        sa.Column("compliance_reason", sa.Text(), nullable=True),
        sa.Column("current_rate_confirmation_id", sa.Integer(), sa.ForeignKey("rate_confirmation_versions.id"), nullable=True),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "load_status_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("load_id", sa.Integer(), sa.ForeignKey("loads.id"), nullable=False),
        sa.Column("from_status", sa.String(40), nullable=True),
        sa.Column("to_status", sa.String(40), nullable=False),
        sa.Column("changed_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "pod_files",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("load_id", sa.Integer(), sa.ForeignKey("loads.id"), nullable=False, unique=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("url", sa.String(255), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("verified_by_user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("entity_type", sa.String(60), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("details", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("organization_id", sa.Integer(), sa.ForeignKey("organizations.id"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("type", sa.String(60), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    for table in [
        "notifications",
        "audit_logs",
        "pod_files",
        "load_status_history",
        "loads",
        "rate_confirmation_versions",
        "carrier_compliance",
        "user_roles",
        "role_permissions",
        "users",
        "roles",
        "permissions",
        "organizations",
    ]:
        op.drop_table(table)
