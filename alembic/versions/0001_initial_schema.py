"""Initial schema — all tables, constraints, indexes, and DB role grants.

Revision ID: 0001
Revises:
Create Date: 2026-06-10
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # USERS
    # ------------------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("badge_id", sa.String(30), nullable=False),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("agency", sa.String(100), nullable=False),
        sa.Column("email", sa.String(200), nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("totp_secret", sa.Text, nullable=True),
        sa.Column("totp_enabled", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("failed_login_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("created_by", sa.String(30), nullable=False),
        sa.UniqueConstraint("badge_id", name="uq_users_badge_id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.CheckConstraint(
            "role IN ('investigator','fsl_officer','fsl_director','court',"
            "'prosecutor','sho','admin','ssoc')",
            name="users_role_check",
        ),
    )
    op.create_index("idx_users_badge_id", "users", ["badge_id"])

    # ------------------------------------------------------------------
    # EVIDENCE  (append-only: no UPDATE, no DELETE via app role)
    # ------------------------------------------------------------------
    op.create_table(
        "evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("case_id", sa.String(50), nullable=False),
        sa.Column("fir_number", sa.String(50), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("evidence_type", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'collected'"),
        sa.Column("collected_by_badge", sa.String(30), nullable=False),
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collection_location", sa.Text, nullable=False),
        sa.Column("hash_sha256", sa.String(64), nullable=False),
        sa.Column("hmac_signature", sa.Text, nullable=False),
        sa.Column("qr_code_data", sa.Text, nullable=True),
        sa.Column("agency", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("created_by", sa.String(30), nullable=False),
        sa.CheckConstraint(
            "evidence_type IN ('digital','physical','biological','document')",
            name="evidence_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('collected','in_transit','at_fsl','report_pending',"
            "'report_ready','returned','disposed')",
            name="evidence_status_check",
        ),
        sa.CheckConstraint(
            r"hash_sha256 ~ '^[a-f0-9]{64}$'",
            name="evidence_hash_hex_check",
        ),
        sa.CheckConstraint(
            r"case_id ~ '^[A-Za-z0-9\-/_]+$'",
            name="evidence_case_id_safe",
        ),
    )
    op.create_index("idx_evidence_case_id", "evidence", ["case_id"])
    op.create_index("idx_evidence_fir_number", "evidence", ["fir_number"])
    op.create_index("idx_evidence_status", "evidence", ["status"])
    op.create_index("idx_evidence_agency", "evidence", ["agency"])

    # ------------------------------------------------------------------
    # CUSTODY TRANSFERS  (append-only: no UPDATE, no DELETE via app role)
    # ------------------------------------------------------------------
    op.create_table(
        "custody_transfers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "evidence_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evidence.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("from_badge", sa.String(30), nullable=False),
        sa.Column("to_badge", sa.String(30), nullable=False),
        sa.Column("from_location", sa.Text, nullable=False),
        sa.Column("to_location", sa.Text, nullable=False),
        sa.Column("transferred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text, nullable=False),
        sa.Column("transfer_hash", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.CheckConstraint("from_badge <> to_badge", name="custody_different_officers"),
        sa.CheckConstraint(
            r"transfer_hash ~ '^[a-f0-9]{64}$'",
            name="custody_hash_hex",
        ),
    )
    op.create_index("idx_custody_evidence_id", "custody_transfers", ["evidence_id"])
    op.create_index("idx_custody_from_badge", "custody_transfers", ["from_badge"])

    # ------------------------------------------------------------------
    # FORENSIC REPORTS
    # ------------------------------------------------------------------
    op.create_table(
        "forensic_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "evidence_id", postgresql.UUID(as_uuid=True),
            sa.ForeignKey("evidence.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("case_id", sa.String(50), nullable=False),
        sa.Column("submitted_by", sa.String(30), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("findings", sa.Text, nullable=False),
        sa.Column("report_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'submitted'"),
        sa.Column("court_reference", sa.Text, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.CheckConstraint(
            "status IN ('submitted','under_review','approved','sent_to_court')",
            name="report_status_check",
        ),
    )
    op.create_index("idx_reports_evidence_id", "forensic_reports", ["evidence_id"])
    op.create_index("idx_reports_status", "forensic_reports", ["status"])

    # ------------------------------------------------------------------
    # AUDIT LOGS  (append-only: no UPDATE, no DELETE via app role)
    # 180-day retention required by CERT-In April 2022 directive.
    # ------------------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("performed_by", sa.String(30), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("ip_address", sa.String(45), nullable=False),   # String supports IPv4 + IPv6
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("outcome", sa.String(10), nullable=False),
        sa.Column("details", postgresql.JSONB, nullable=False, server_default="'{}'"),
        sa.Column("request_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint(
            "outcome IN ('success','failure','pending')",
            name="audit_outcome_check",
        ),
    )
    op.create_index("idx_audit_performed_by", "audit_logs", ["performed_by"])
    op.create_index("idx_audit_performed_at", "audit_logs", ["performed_at"])
    op.create_index("idx_audit_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("idx_audit_action", "audit_logs", ["action"])

    # ------------------------------------------------------------------
    # JWT DENYLIST
    # ------------------------------------------------------------------
    op.create_table(
        "jwt_denylist",
        sa.Column("jti", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("NOW()")),
        sa.Column("revoked_by", sa.String(30), nullable=False),
    )
    op.create_index("idx_jwt_expires", "jwt_denylist", ["expires_at"])

    # ------------------------------------------------------------------
    # DB ROLE AND PERMISSION GRANTS
    # Append-only enforcement at the database level — independent of app code.
    # If the application server is compromised, these grants still hold.
    # ------------------------------------------------------------------
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT FROM pg_catalog.pg_roles WHERE rolname = 'forenchain_app'
            ) THEN
                CREATE ROLE forenchain_app LOGIN PASSWORD 'changeme-in-deployment';
            END IF;
        END
        $$;
    """)

    # Evidence: INSERT only — no UPDATE, no DELETE ever
    op.execute("GRANT SELECT, INSERT ON evidence TO forenchain_app")

    # Custody transfers: INSERT only — chain is append-only
    op.execute("GRANT SELECT, INSERT ON custody_transfers TO forenchain_app")

    # Audit logs: INSERT only — no modification permitted
    op.execute("GRANT SELECT, INSERT ON audit_logs TO forenchain_app")

    # Reports: UPDATE allowed for status transitions only
    op.execute("GRANT SELECT, INSERT, UPDATE ON forensic_reports TO forenchain_app")

    # Users: full write access (admin operations)
    op.execute("GRANT SELECT, INSERT, UPDATE ON users TO forenchain_app")

    # JWT denylist: INSERT only (revocations are permanent)
    op.execute("GRANT SELECT, INSERT ON jwt_denylist TO forenchain_app")


def downgrade() -> None:
    op.execute("REVOKE ALL ON evidence FROM forenchain_app")
    op.execute("REVOKE ALL ON custody_transfers FROM forenchain_app")
    op.execute("REVOKE ALL ON audit_logs FROM forenchain_app")
    op.execute("REVOKE ALL ON forensic_reports FROM forenchain_app")
    op.execute("REVOKE ALL ON users FROM forenchain_app")
    op.execute("REVOKE ALL ON jwt_denylist FROM forenchain_app")

    op.drop_table("jwt_denylist")
    op.drop_table("audit_logs")
    op.drop_table("forensic_reports")
    op.drop_table("custody_transfers")
    op.drop_table("evidence")
    op.drop_table("users")
