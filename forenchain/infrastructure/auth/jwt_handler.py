from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from jose import JWTError, jwt

from forenchain.config import get_settings


def create_access_token(badge_id: str, role: str, agency: str) -> tuple[str, str]:
    """Return (encoded_token, jti)."""
    settings = get_settings()
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.access_token_expire_minutes)

    payload: dict[str, Any] = {
        "sub": badge_id,
        "role": role,
        "agency": agency,
        "jti": jti,
        "iat": now,
        "exp": expire,
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify token. Raises JWTError on failure."""
    settings = get_settings()
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
