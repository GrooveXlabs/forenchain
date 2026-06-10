"""
Mapper functions between SQLAlchemy ORM rows and domain models.

These are explicit functions — no magic, no metaclasses.
Domain models are immutable Pydantic objects; ORM rows are mutable SQLAlchemy objects.
They must never be the same object.

One rule: domain → ORM never goes through the domain model's validators again.
          ORM → domain always constructs a fresh domain model (validates on creation).
"""

from __future__ import annotations

import uuid
from datetime import timezone

from forenchain.domain.models.audit import AuditAction, AuditLog, AuditOutcome
from forenchain.domain.models.custody import CustodyTransfer
from forenchain.domain.models.evidence import Evidence, EvidenceStatus, EvidenceType
from forenchain.domain.models.user import User, UserRole
from forenchain.infrastructure.database import tables as t


def _ensure_tz(dt):
    """PostgreSQL may return naive datetimes — attach UTC if so."""
    if dt is None:
        return dt
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


# -----------------------------------------------------------------------
# Evidence
# -----------------------------------------------------------------------

def evidence_to_row(evidence: Evidence, agency: str, created_by: str) -> dict:
    return {
        "id": evidence.id,
        "case_id": evidence.case_id,
        "fir_number": evidence.fir_number,
        "description": evidence.description,
        "evidence_type": evidence.evidence_type.value,
        "status": evidence.status.value,
        "collected_by_badge": evidence.collected_by_badge,
        "collected_at": evidence.collected_at,
        "collection_location": evidence.collection_location,
        "hash_sha256": evidence.hash_sha256,
        "hmac_signature": evidence.hmac_signature,
        "qr_code_data": evidence.qr_code_data,
        "agency": agency,
        "created_by": created_by,
    }


def row_to_evidence(row: t.EvidenceTable) -> Evidence:
    return Evidence(
        id=row.id,
        case_id=row.case_id,
        fir_number=row.fir_number,
        description=row.description,
        evidence_type=EvidenceType(row.evidence_type),
        status=EvidenceStatus(row.status),
        collected_by_badge=row.collected_by_badge,
        collected_at=_ensure_tz(row.collected_at),
        collection_location=row.collection_location,
        hash_sha256=row.hash_sha256,
        hmac_signature=row.hmac_signature,
        qr_code_data=row.qr_code_data,
        created_at=_ensure_tz(row.created_at),
    )


# -----------------------------------------------------------------------
# Custody transfer
# -----------------------------------------------------------------------

def transfer_to_row(transfer: CustodyTransfer) -> dict:
    return {
        "id": transfer.id,
        "evidence_id": transfer.evidence_id,
        "from_badge": transfer.from_badge,
        "to_badge": transfer.to_badge,
        "from_location": transfer.from_location,
        "to_location": transfer.to_location,
        "transferred_at": transfer.transferred_at,
        "reason": transfer.reason,
        "transfer_hash": transfer.transfer_hash,
    }


def row_to_transfer(row: t.CustodyTransferTable) -> CustodyTransfer:
    return CustodyTransfer(
        id=row.id,
        evidence_id=row.evidence_id,
        from_badge=row.from_badge,
        to_badge=row.to_badge,
        from_location=row.from_location,
        to_location=row.to_location,
        transferred_at=_ensure_tz(row.transferred_at),
        reason=row.reason,
        transfer_hash=row.transfer_hash,
        created_at=_ensure_tz(row.created_at),
    )


# -----------------------------------------------------------------------
# Audit log
# -----------------------------------------------------------------------

def audit_to_row(log: AuditLog) -> dict:
    return {
        "id": log.id,
        "action": log.action.value,
        "performed_by": log.performed_by,
        "performed_at": log.performed_at,
        "ip_address": str(log.ip_address),
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "outcome": log.outcome.value,
        "details": log.details,
        "request_id": log.request_id,
    }


def row_to_audit(row: t.AuditLogTable) -> AuditLog:
    return AuditLog(
        id=row.id,
        action=AuditAction(row.action),
        performed_by=row.performed_by,
        performed_at=_ensure_tz(row.performed_at),
        ip_address=str(row.ip_address),
        entity_type=row.entity_type,
        entity_id=row.entity_id,
        outcome=AuditOutcome(row.outcome),
        details=row.details or {},
        request_id=row.request_id,
    )


# -----------------------------------------------------------------------
# User
# -----------------------------------------------------------------------

def user_to_row(user: User) -> dict:
    return {
        "id": user.id,
        "badge_id": user.badge_id,
        "full_name": user.full_name,
        "role": user.role.value,
        "agency": user.agency,
        "email": str(user.email),
        "password_hash": user.password_hash,
        "totp_secret": user.totp_secret,
        "totp_enabled": user.totp_enabled,
        "is_active": user.is_active,
        "failed_login_count": user.failed_login_count,
        "locked_until": user.locked_until,
        "created_by": user.created_by,
    }


def row_to_user(row: t.UserTable) -> User:
    return User(
        id=row.id,
        badge_id=row.badge_id,
        full_name=row.full_name,
        role=UserRole(row.role),
        agency=row.agency,
        email=row.email,
        password_hash=row.password_hash,
        totp_secret=row.totp_secret,
        totp_enabled=row.totp_enabled,
        is_active=row.is_active,
        failed_login_count=row.failed_login_count,
        locked_until=_ensure_tz(row.locked_until),
        created_at=_ensure_tz(row.created_at),
        created_by=row.created_by,
    )
