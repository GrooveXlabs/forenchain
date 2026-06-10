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
    USER_LOGOUT = "user.logout"
    USER_CREATED = "user.created"
    ACCESS_DENIED = "access.denied"


class AuditOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING = "pending"   # intent recorded before action executes


class AuditLog(BaseModel):
    """
    Immutable record of every action performed in the system.

    Written BEFORE the action executes. If the action fails, a second entry
    records the failure outcome. No entry is ever modified or deleted.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    action: AuditAction
    performed_by: str
    performed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ip_address: str
    entity_type: str
    entity_id: Optional[uuid.UUID] = None
    outcome: AuditOutcome
    details: dict[str, Any] = Field(default_factory=dict)
    request_id: uuid.UUID = Field(default_factory=uuid.uuid4)

    model_config = {"frozen": True}
