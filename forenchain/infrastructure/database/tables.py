"""
SQLAlchemy ORM table definitions.

These are NOT domain models. They are the infrastructure representation.
The repositories map between these tables and the domain models.

Important: No domain model is imported here. No Pydantic model appears here.
This keeps the domain layer independent of SQLAlchemy.
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, ForeignKey,
    Index, Integer, String, Text, UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class UserTable(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    badge_id = Column(String(30), nullable=False, unique=True, index=True)
    full_name = Column(String(200), nullable=False)
    role = Column(String(20), nullable=False)
    agency = Column(String(100), nullable=False)
    email = Column(String(200), nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    totp_secret = Column(Text, nullable=True)
    totp_enabled = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    failed_login_count = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(String(30), nullable=False)

    __table_args__ = (
        CheckConstraint(
            "role IN ('investigator','fsl_officer','fsl_director','court','prosecutor','sho','admin','ssoc')",
            name="users_role_check",
        ),
    )


class EvidenceTable(Base):
    __tablename__ = "evidence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(String(50), nullable=False, index=True)
    fir_number = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=False)
    evidence_type = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="collected")
    collected_by_badge = Column(String(30), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False)
    collection_location = Column(Text, nullable=False)
    hash_sha256 = Column(String(64), nullable=False)
    hmac_signature = Column(Text, nullable=False)
    qr_code_data = Column(Text, nullable=True)
    agency = Column(String(100), nullable=False)  # for Row-Level Security
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    created_by = Column(String(30), nullable=False)

    custody_transfers = relationship("CustodyTransferTable", back_populates="evidence")
    forensic_reports = relationship("ForensicReportTable", back_populates="evidence")

    __table_args__ = (
        CheckConstraint(
            "evidence_type IN ('digital','physical','biological','document')",
            name="evidence_type_check",
        ),
        CheckConstraint(
            "status IN ('collected','in_transit','at_fsl','report_pending','report_ready','returned','disposed')",
            name="evidence_status_check",
        ),
        CheckConstraint(
            r"hash_sha256 ~ '^[a-f0-9]{64}$'",
            name="evidence_hash_hex_check",
        ),
        CheckConstraint(
            r"case_id ~ '^[A-Za-z0-9\-/_]+$'",
            name="evidence_case_id_safe",
        ),
    )


class CustodyTransferTable(Base):
    __tablename__ = "custody_transfers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False, index=True)
    from_badge = Column(String(30), nullable=False, index=True)
    to_badge = Column(String(30), nullable=False, index=True)
    from_location = Column(Text, nullable=False)
    to_location = Column(Text, nullable=False)
    transferred_at = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text, nullable=False)
    transfer_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    evidence = relationship("EvidenceTable", back_populates="custody_transfers")

    __table_args__ = (
        CheckConstraint("from_badge <> to_badge", name="custody_different_officers"),
        CheckConstraint(r"transfer_hash ~ '^[a-f0-9]{64}$'", name="custody_hash_hex"),
    )


class ForensicReportTable(Base):
    __tablename__ = "forensic_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evidence_id = Column(UUID(as_uuid=True), ForeignKey("evidence.id"), nullable=False, index=True)
    case_id = Column(String(50), nullable=False)
    submitted_by = Column(String(30), nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    report_type = Column(String(50), nullable=False)
    summary = Column(Text, nullable=False)
    findings = Column(Text, nullable=False)
    report_hash = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="submitted")
    court_reference = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    evidence = relationship("EvidenceTable", back_populates="forensic_reports")

    __table_args__ = (
        CheckConstraint(
            "status IN ('submitted','under_review','approved','sent_to_court')",
            name="report_status_check",
        ),
    )


class AuditLogTable(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action = Column(String(50), nullable=False, index=True)
    performed_by = Column(String(30), nullable=False, index=True)
    performed_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), index=True)
    ip_address = Column(String(45), nullable=False)   # VARCHAR — supports IPv4 + IPv6
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    outcome = Column(String(10), nullable=False)
    details = Column(JSONB, nullable=False, default=dict)
    request_id = Column(UUID(as_uuid=True), nullable=False)

    __table_args__ = (
        CheckConstraint("outcome IN ('success','failure','pending')", name="audit_outcome_check"),
        Index("idx_audit_entity", "entity_type", "entity_id"),
    )


class JWTDenylistTable(Base):
    __tablename__ = "jwt_denylist"

    jti = Column(UUID(as_uuid=True), primary_key=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    revoked_by = Column(String(30), nullable=False)
