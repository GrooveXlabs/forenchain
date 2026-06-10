from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forenchain.application.ports.evidence_repository import EvidenceRepository
from forenchain.domain.models.evidence import Evidence
from forenchain.infrastructure.database.mappers import evidence_to_row, row_to_evidence
from forenchain.infrastructure.database.tables import EvidenceTable


class PostgresEvidenceRepository(EvidenceRepository):
    """Append-only PostgreSQL implementation. forenchain_app role has no UPDATE/DELETE on evidence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, evidence: Evidence, agency: str, created_by: str) -> Evidence:
        row = EvidenceTable(**evidence_to_row(evidence, agency, created_by))
        self._session.add(row)
        await self._session.flush()   # get server defaults (created_at) without committing
        await self._session.refresh(row)
        return row_to_evidence(row)

    async def get_by_id(self, evidence_id: uuid.UUID) -> Optional[Evidence]:
        result = await self._session.execute(
            select(EvidenceTable).where(EvidenceTable.id == evidence_id)
        )
        row = result.scalar_one_or_none()
        return row_to_evidence(row) if row else None

    async def list_by_case(self, case_id: str, limit: int = 50, offset: int = 0) -> list[Evidence]:
        result = await self._session.execute(
            select(EvidenceTable)
            .where(EvidenceTable.case_id == case_id)
            .order_by(EvidenceTable.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [row_to_evidence(r) for r in result.scalars().all()]

    async def list_by_fir(self, fir_number: str, limit: int = 50, offset: int = 0) -> list[Evidence]:
        result = await self._session.execute(
            select(EvidenceTable)
            .where(EvidenceTable.fir_number == fir_number)
            .order_by(EvidenceTable.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [row_to_evidence(r) for r in result.scalars().all()]
