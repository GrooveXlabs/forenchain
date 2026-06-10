from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from forenchain.domain.models.evidence import Evidence


class EvidenceRepository(ABC):
    """Port interface for evidence persistence. Infrastructure implements this."""

    @abstractmethod
    async def create(self, evidence: Evidence, agency: str, created_by: str) -> Evidence:
        """Persist a new evidence record. agency is set for Row-Level Security."""

    @abstractmethod
    async def get_by_id(self, evidence_id: uuid.UUID) -> Optional[Evidence]:
        """Return evidence or None if not found."""

    @abstractmethod
    async def list_by_case(self, case_id: str, limit: int = 50, offset: int = 0) -> list[Evidence]:
        """Return all evidence for a case, newest first."""

    @abstractmethod
    async def list_by_fir(self, fir_number: str, limit: int = 50, offset: int = 0) -> list[Evidence]:
        """Return all evidence for an FIR number."""
