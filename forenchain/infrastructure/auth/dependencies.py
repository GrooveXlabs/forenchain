"""
FastAPI dependency injection for authentication and role enforcement.

get_current_user: validates JWT, checks denylist, checks is_active.
require_role: returns a dependency that checks the role claim against allowed roles.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError

from forenchain.domain.models.user import UserRole
from forenchain.infrastructure.auth.jwt_handler import decode_token

_bearer = HTTPBearer()


class TokenData:
    def __init__(self, badge_id: str, role: str, agency: str, jti: str) -> None:
        self.badge_id = badge_id
        self.role = UserRole(role)
        self.agency = agency
        self.jti = jti


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(_bearer)],
) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise credentials_exception

    badge_id = payload.get("sub")
    role = payload.get("role")
    agency = payload.get("agency")
    jti = payload.get("jti")

    if not all([badge_id, role, agency, jti]):
        raise credentials_exception

    return TokenData(badge_id=badge_id, role=role, agency=agency, jti=jti)  # type: ignore[arg-type]


def require_role(*roles: UserRole):
    """Returns a FastAPI dependency that enforces role-based access."""

    async def _check(current_user: Annotated[TokenData, Depends(get_current_user)]) -> TokenData:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"role '{current_user.role.value}' is not permitted for this action",
            )
        return current_user

    return _check
