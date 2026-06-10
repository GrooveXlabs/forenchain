from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field, model_validator


class CustodyTransfer(BaseModel):
    """
    A single transfer of evidence from one officer/location to another.

    The chain is append-only. No transfer record is ever modified or deleted.
    Attempting to update a transfer raises an error at the service layer.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    evidence_id: uuid.UUID
    from_badge: str = Field(min_length=1, max_length=30)
    to_badge: str = Field(min_length=1, max_length=30)
    from_location: str = Field(min_length=1, max_length=200)
    to_location: str = Field(min_length=1, max_length=200)
    transferred_at: datetime
    reason: str = Field(min_length=3, max_length=500)
    transfer_hash: str = Field(min_length=64, max_length=64)  # SHA-256 of transfer data
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"frozen": True}  # append-only enforced at model level

    @model_validator(mode="after")
    def from_and_to_must_differ(self) -> "CustodyTransfer":
        if self.from_badge == self.to_badge:
            raise ValueError("from_badge and to_badge cannot be the same officer")
        return self


class CustodyTransferRequest(BaseModel):
    """Input accepted from an officer initiating a custody transfer."""

    evidence_id: uuid.UUID
    to_badge: str = Field(min_length=1, max_length=30)
    to_location: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=3, max_length=500)
