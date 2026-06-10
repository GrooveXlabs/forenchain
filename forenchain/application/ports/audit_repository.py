from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from forenchain.domain.models.audit import AuditLog, AuditAction


class AuditRepository(ABC):
    """Port interface for audit log persistence. Append-only, write-before-action."""

    @abstractmethod
    async def append(self, log: AuditLog) -> AuditLog:
        """Write an audit log entry. Must be called before the audited action executes."""

    @abstractmethod
    async def list_by_entity(
        self, entity_type: str, entity_id: uuid.UUID, limit: int = 100
    ) -> list[AuditLog]:
        """Return audit history for a specific entity, newest first."""

    @abstractmethod
    async def list_by_actor(
        self, badge_id: str, limit: int = 100, offset: int = 0
    ) -> list[AuditLog]:
        """Return all actions taken by a specific officer."""
