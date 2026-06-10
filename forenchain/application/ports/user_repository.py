from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Optional

from forenchain.domain.models.user import User


class UserRepository(ABC):
    """Port interface for user persistence."""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Persist a new user. Raises if badge_id or email already exists."""

    @abstractmethod
    async def get_by_badge(self, badge_id: str) -> Optional[User]:
        """Return user by badge_id, or None."""

    @abstractmethod
    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Return user by id, or None."""

    @abstractmethod
    async def update_login_state(
        self,
        badge_id: str,
        failed_count: int,
        locked_until: Optional[object] = None,
    ) -> None:
        """Update failed_login_count and locked_until after login attempt."""

    @abstractmethod
    async def set_totp_enabled(self, badge_id: str, secret: str) -> None:
        """Store TOTP secret and set totp_enabled=True."""

    @abstractmethod
    async def set_active(self, badge_id: str, is_active: bool) -> None:
        """Suspend or reinstate a user account."""
