"""
Audit-before-action pattern.

An audit log entry is written BEFORE the action executes.
If the action fails, a failure outcome is recorded in a second entry.
If writing the audit log fails, the action does not execute.

This ensures: every attempted action has an audit record, even failed ones.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from functools import wraps
from typing import Any, Callable

from forenchain.domain.models.audit import AuditAction, AuditLog
from forenchain.application.ports.audit_repository import AuditRepository


async def write_audit(
    audit_repo: AuditRepository,
    action: AuditAction,
    performed_by: str,
    ip_address: str,
    entity_type: str,
    outcome: str,
    entity_id: uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
    request_id: uuid.UUID | None = None,
) -> AuditLog:
    log = AuditLog(
        action=action,
        performed_by=performed_by,
        performed_at=datetime.now(timezone.utc),
        ip_address=ip_address,
        entity_type=entity_type,
        entity_id=entity_id,
        outcome=outcome,
        details=details or {},
        request_id=request_id or uuid.uuid4(),
    )
    return await audit_repo.append(log)
