from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from forenchain.domain.models.custody import CustodyTransfer


class CustodyRepository(ABC):
    """Port interface for custody transfer persistence. Append-only."""

    @abstractmethod
    async def append(self, transfer: CustodyTransfer) -> CustodyTransfer:
        """Append a new custody transfer. No update, no delete."""

    @abstractmethod
    async def get_chain(self, evidence_id: uuid.UUID) -> list[CustodyTransfer]:
        """Return full custody chain for evidence, ordered oldest to newest."""

    @abstractmethod
    async def get_latest(self, evidence_id: uuid.UUID) -> Optional[CustodyTransfer]:
        """Return the most recent custody transfer, or None if no transfers yet."""
