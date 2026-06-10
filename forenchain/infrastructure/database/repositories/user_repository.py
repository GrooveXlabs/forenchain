from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from forenchain.application.ports.user_repository import UserRepository
from forenchain.domain.models.user import User
from forenchain.infrastructure.database.mappers import row_to_user, user_to_row
from forenchain.infrastructure.database.tables import UserTable


class PostgresUserRepository(UserRepository):

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user: User) -> User:
        row = UserTable(**user_to_row(user))
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return row_to_user(row)

    async def get_by_badge(self, badge_id: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserTable).where(UserTable.badge_id == badge_id)
        )
        row = result.scalar_one_or_none()
        return row_to_user(row) if row else None

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        result = await self._session.execute(
            select(UserTable).where(UserTable.id == user_id)
        )
        row = result.scalar_one_or_none()
        return row_to_user(row) if row else None

    async def update_login_state(
        self,
        badge_id: str,
        failed_count: int,
        locked_until: Optional[datetime] = None,
    ) -> None:
        await self._session.execute(
            update(UserTable)
            .where(UserTable.badge_id == badge_id)
            .values(failed_login_count=failed_count, locked_until=locked_until)
        )

    async def set_totp_enabled(self, badge_id: str, secret: str) -> None:
        await self._session.execute(
            update(UserTable)
            .where(UserTable.badge_id == badge_id)
            .values(totp_secret=secret, totp_enabled=True)
        )

    async def set_active(self, badge_id: str, is_active: bool) -> None:
        await self._session.execute(
            update(UserTable)
            .where(UserTable.badge_id == badge_id)
            .values(is_active=is_active)
        )
