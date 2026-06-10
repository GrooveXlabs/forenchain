from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class AuditAction(str, Enum):
    EVIDENCE_CREATED = "evidence.created"
    EVIDENCE_VIEWED = "evidence.viewed"
    CUSTODY_TRANSFERRED = "custody.transferred"
    CUSTODY_CHAIN_VIEWED = "custody.chain.viewed"
    REPORT_SUBMITTED = "report.submitted"
    REPORT_VIEWED = "report.viewed"
    USER_LOGIN = "user.login"
    USER_LOGIN_FAILED = "user.login.failed"
    USER_CREATED = "user.created"
    ACCESS_DENIED = "access.denied"


class AuditLog(BaseModel):
    """
    Immutable record of every action performed in the system.

    Written BEFORE the action executes. If the action fails, the failed
    outcome is recorded in a follow-up log entry. No entry is ever deleted.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    action: AuditAction
    performed_by: str  # badge ID or system identifier
    performed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: str
    entity_type: str  # e.g. "evidence", "custody_transfer"
    entity_id: Optional[uuid.UUID] = None
    outcome: str  # "success" or "failure"
    details: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}  # audit logs are never modified
