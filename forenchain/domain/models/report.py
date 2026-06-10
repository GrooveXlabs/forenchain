from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ReportStatus(str, Enum):
    SUBMITTED = "submitted"         # FSL officer submitted, pending review
    UNDER_REVIEW = "under_review"   # FSL Director is reviewing
    APPROVED = "approved"           # FSL Director approved, ready for court
    SENT_TO_COURT = "sent_to_court" # Formally transmitted to court


# Valid forward-only transitions. Backward transitions are rejected.
VALID_TRANSITIONS: dict[ReportStatus, list[ReportStatus]] = {
    ReportStatus.SUBMITTED: [ReportStatus.UNDER_REVIEW],
    ReportStatus.UNDER_REVIEW: [ReportStatus.APPROVED],
    ReportStatus.APPROVED: [ReportStatus.SENT_TO_COURT],
    ReportStatus.SENT_TO_COURT: [],  # terminal state
}


def is_valid_transition(current: ReportStatus, next_status: ReportStatus) -> bool:
    return next_status in VALID_TRANSITIONS.get(current, [])


class ForensicReport(BaseModel):
    """
    A forensic analysis report submitted by an FSL officer.

    report_hash is computed server-side from summary + findings.
    Status transitions are forward-only — defined in VALID_TRANSITIONS.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    evidence_id: uuid.UUID
    case_id: str = Field(min_length=1, max_length=50)
    submitted_by: str = Field(min_length=1, max_length=30)  # badge_id
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    report_type: str = Field(min_length=2, max_length=50)
    summary: str = Field(min_length=10, max_length=2000)
    findings: str = Field(min_length=10)
    report_hash: str = Field(min_length=64, max_length=64)
    status: ReportStatus = ReportStatus.SUBMITTED
    court_reference: Optional[str] = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"frozen": True}


class ReportSubmitRequest(BaseModel):
    """Input accepted from an FSL officer submitting a report."""

    evidence_id: uuid.UUID
    case_id: str = Field(min_length=1, max_length=50)
    report_type: str = Field(min_length=2, max_length=50)
    summary: str = Field(min_length=10, max_length=2000)
    findings: str = Field(min_length=10)


class ReportStatusUpdateRequest(BaseModel):
    """Input for transitioning a report's status."""

    new_status: ReportStatus
    court_reference: Optional[str] = Field(default=None, max_length=100)
