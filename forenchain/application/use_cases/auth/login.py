"""
LoginUseCase — validates credentials and issues a JWT.

Steps (in order — if any step fails, subsequent steps do not execute):
1. Look up user by badge_id. If not found: write FAILED audit, return 401.
2. Check account not locked. If locked: write FAILED audit, return 423.
3. Verify password with bcrypt. If wrong: increment failed_count, write FAILED audit, return 401.
4. Check TOTP is provisioned. If not: write FAILED audit, return 403.
5. Verify TOTP code. If wrong: write FAILED audit, return 401.
6. Reset failed_login_count to 0.
7. Issue JWT with badge_id, role, agency, jti, exp=15min.
8. Write SUCCESS audit.
9. Return token.

The response body for steps 1 and 3 is identical: "invalid credentials".
This prevents user enumeration — an attacker cannot distinguish "no such user" from "wrong password".
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Protocol

from forenchain.application.ports.audit_repository import AuditRepository
from forenchain.application.ports.user_repository import UserRepository
from forenchain.application.services.audit_service import write_audit
from forenchain.domain.models.audit import AuditAction
from forenchain.domain.models.user import User


class PasswordHandler(Protocol):
    def verify(self, plain: str, hashed: str) -> bool: ...


class TOTPHandler(Protocol):
    def verify(self, secret: str, code: str) -> bool: ...


class TokenHandler(Protocol):
    def create_access_token(self, badge_id: str, role: str, agency: str) -> tuple[str, str]: ...


class InvalidCredentialsError(Exception):
    pass


class AccountLockedError(Exception):
    def __init__(self, locked_until: datetime) -> None:
        self.locked_until = locked_until
        super().__init__(f"Account locked until {locked_until.isoformat()}")


class TOTPNotProvisionedError(Exception):
    pass


class LoginUseCase:
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_MINUTES = 15

    def __init__(
        self,
        user_repo: UserRepository,
        audit_repo: AuditRepository,
        password_handler: PasswordHandler,
        totp_handler: TOTPHandler,
        token_handler: TokenHandler,
    ) -> None:
        self._user_repo = user_repo
        self._audit_repo = audit_repo
        self._password = password_handler
        self._totp = totp_handler
        self._token = token_handler

    async def execute(
        self,
        badge_id: str,
        password: str,
        totp_code: str,
        ip_address: str,
        request_id: uuid.UUID,
    ) -> tuple[str, str]:  # (access_token, jti)
        async def fail(reason: str, details: dict | None = None) -> None:
            await write_audit(
                audit_repo=self._audit_repo,
                action=AuditAction.USER_LOGIN_FAILED,
                performed_by=badge_id,
                ip_address=ip_address,
                entity_type="user",
                outcome="failure",
                details={"reason": reason, **(details or {})},
                request_id=request_id,
            )

        user = await self._user_repo.get_by_badge(badge_id)
        if user is None:
            await fail("user_not_found")
            raise InvalidCredentialsError("invalid credentials")

        if user.is_locked():
            await fail("account_locked", {"locked_until": str(user.locked_until)})
            raise AccountLockedError(user.locked_until)  # type: ignore[arg-type]

        if not self._password.verify(password, user.password_hash):
            new_count = user.failed_login_count + 1
            locked_until = None
            if new_count >= self.MAX_FAILED_ATTEMPTS:
                locked_until = datetime.now(timezone.utc) + timedelta(minutes=self.LOCKOUT_MINUTES)
            await self._user_repo.update_login_state(badge_id, new_count, locked_until)
            await fail("wrong_password", {"failed_count": new_count})
            raise InvalidCredentialsError("invalid credentials")

        if not user.totp_enabled:
            await fail("totp_not_provisioned")
            raise TOTPNotProvisionedError("MFA not configured for this account")

        if not self._totp.verify(user.totp_secret or "", totp_code):  # type: ignore[arg-type]
            await fail("totp_invalid")
            raise InvalidCredentialsError("invalid credentials")

        # All checks passed — reset failed count and issue token.
        await self._user_repo.update_login_state(badge_id, 0, None)

        access_token, jti = self._token.create_access_token(
            badge_id=badge_id,
            role=user.role.value,
            agency=user.agency,
        )

        await write_audit(
            audit_repo=self._audit_repo,
            action=AuditAction.USER_LOGIN,
            performed_by=badge_id,
            ip_address=ip_address,
            entity_type="user",
            outcome="success",
            details={"role": user.role.value, "agency": user.agency},
            request_id=request_id,
        )

        return access_token, jti
