from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class EvidenceType(str, Enum):
    DIGITAL = "digital"       # drives, phones, USBs
    PHYSICAL = "physical"     # weapons, documents, samples
    BIOLOGICAL = "biological" # DNA, blood, fingerprints
    DOCUMENT = "document"     # paper records, photographs


class EvidenceStatus(str, Enum):
    COLLECTED = "collected"
    IN_TRANSIT = "in_transit"
    AT_FSL = "at_fsl"
    REPORT_PENDING = "report_pending"
    REPORT_READY = "report_ready"
    RETURNED = "returned"
    DISPOSED = "disposed"


class Evidence(BaseModel):
    """
    A single piece of evidence in a case.

    The hash field is the SHA-256 of the evidence descriptor — it is computed
    server-side at creation and must never be accepted from a client.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    case_id: str = Field(min_length=1, max_length=50)
    fir_number: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=3, max_length=500)
    evidence_type: EvidenceType
    status: EvidenceStatus = EvidenceStatus.COLLECTED
    collected_by_badge: str = Field(min_length=1, max_length=30)
    collected_at: datetime
    collection_location: str = Field(min_length=3, max_length=200)
    hash_sha256: str = Field(min_length=64, max_length=64)
    hmac_signature: str = Field(min_length=1)
    qr_code_data: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"frozen": True}  # immutable after creation

    @field_validator("hash_sha256")
    @classmethod
    def hash_must_be_hex(cls, v: str) -> str:
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("hash_sha256 must be a valid hex string")
        return v.lower()

    @field_validator("case_id", "fir_number")
    @classmethod
    def no_special_chars(cls, v: str) -> str:
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/_")
        if not all(c in allowed for c in v):
            raise ValueError("ID contains invalid characters")
        return v


class EvidenceCreateRequest(BaseModel):
    """Input accepted from an officer creating an evidence record."""

    case_id: str = Field(min_length=1, max_length=50)
    fir_number: str = Field(min_length=1, max_length=50)
    description: str = Field(min_length=3, max_length=500)
    evidence_type: EvidenceType
    collected_by_badge: str = Field(min_length=1, max_length=30)
    collected_at: datetime
    collection_location: str = Field(min_length=3, max_length=200)

    @field_validator("case_id", "fir_number")
    @classmethod
    def no_special_chars(cls, v: str) -> str:
        allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-/_")
        if not all(c in allowed for c in v):
            raise ValueError("ID contains invalid characters")
        return v
