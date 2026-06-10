from __future__ import annotations

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from forenchain.application.ports.custody_repository import CustodyRepository
from forenchain.domain.models.custody import CustodyTransfer
from forenchain.infrastructure.database.mappers import row_to_transfer, transfer_to_row
from forenchain.infrastructure.database.tables import CustodyTransferTable


class PostgresCustodyRepository(CustodyRepository):
    """Append-only PostgreSQL implementation. forenchain_app role has no UPDATE/DELETE."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def append(self, transfer: CustodyTransfer) -> CustodyTransfer:
        row = CustodyTransferTable(**transfer_to_row(transfer))
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_transfer(row)

    async def get_chain(self, evidence_id: uuid.UUID) -> list[CustodyTransfer]:
        result = await self._session.execute(
            select(CustodyTransferTable)
            .where(CustodyTransferTable.evidence_id == evidence_id)
            .order_by(CustodyTransferTable.transferred_at.asc())
        )
        return [row_to_transfer(r) for r in result.scalars().all()]

    async def get_latest(self, evidence_id: uuid.UUID) -> Optional[CustodyTransfer]:
        result = await self._session.execute(
            select(CustodyTransferTable)
            .where(CustodyTransferTable.evidence_id == evidence_id)
            .order_by(CustodyTransferTable.transferred_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        return row_to_transfer(row) if row else None
