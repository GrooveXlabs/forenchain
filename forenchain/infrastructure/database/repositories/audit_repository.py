from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forenchain.application.ports.audit_repository import AuditRepository
from forenchain.domain.models.audit import AuditLog
from forenchain.infrastructure.database.mappers import audit_to_row, row_to_audit
from forenchain.infrastructure.database.tables import AuditLogTable


class PostgresAuditRepository(AuditRepository):
    """Append-only PostgreSQL implementation.
    forenchain_app role has SELECT+INSERT only — no UPDATE, no DELETE.
    pgaudit provides a second, independent WAL-level audit trail.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, log: AuditLog) -> AuditLog:
        row = AuditLogTable(**audit_to_row(log))
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_audit(row)

    async def list_by_entity(
        self, entity_type: str, entity_id: uuid.UUID, limit: int = 100
    ) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLogTable)
            .where(
                AuditLogTable.entity_type == entity_type,
                AuditLogTable.entity_id == entity_id,
            )
            .order_by(AuditLogTable.performed_at.desc())
            .limit(limit)
        )
        return [row_to_audit(r) for r in result.scalars().all()]

    async def list_by_actor(
        self, badge_id: str, limit: int = 100, offset: int = 0
    ) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLogTable)
            .where(AuditLogTable.performed_by == badge_id)
            .order_by(AuditLogTable.performed_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return [row_to_audit(r) for r in result.scalars().all()]
