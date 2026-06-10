from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserRole(str, Enum):
    INVESTIGATOR = "investigator"   # Investigating officer — creates evidence, initiates transfers
    FSL_OFFICER = "fsl_officer"     # FSL analyst — receives evidence, submits reports
    FSL_DIRECTOR = "fsl_director"   # FSL head — approves reports before court submission
    COURT = "court"                 # Read-only — case status and report availability only
    PROSECUTOR = "prosecutor"       # Read-only — case summary and evidence status
    SHO = "sho"                     # Station House Officer — station-level oversight
    ADMIN = "admin"                 # User management, audit log access, system config
    SSOC = "ssoc"                   # State SOC analyst — security monitoring, audit logs


class User(BaseModel):
    """
    An authenticated user of the ForenChain system.

    Password hash and TOTP secret are never returned in API responses.
    They exist here only for the auth layer to validate credentials.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    badge_id: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=2, max_length=200)
    role: UserRole
    agency: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password_hash: str
    totp_secret: Optional[str] = None
    totp_enabled: bool = False
    is_active: bool = True
    failed_login_count: int = Field(default=0, ge=0)
    locked_until: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str  # badge_id of the admin who created this account

    model_config = {"frozen": True}

    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    def can_write(self) -> bool:
        return self.role in (
            UserRole.INVESTIGATOR,
            UserRole.FSL_OFFICER,
            UserRole.FSL_DIRECTOR,
            UserRole.ADMIN,
        )

    def is_read_only(self) -> bool:
        return self.role in (UserRole.COURT, UserRole.PROSECUTOR)


class UserCreateRequest(BaseModel):
    """Input accepted by an admin when creating a new user account."""

    badge_id: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=2, max_length=200)
    role: UserRole
    agency: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class UserPublic(BaseModel):
    """Safe user representation — no password hash or TOTP secret."""

    id: uuid.UUID
    badge_id: str
    full_name: str
    role: UserRole
    agency: str
    email: str
    is_active: bool
    totp_enabled: bool
    created_at: datetime
