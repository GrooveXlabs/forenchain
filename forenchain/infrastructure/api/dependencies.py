"""
FastAPI dependency providers for repositories and use cases.

Each request gets its own AsyncSession (from get_db_session).
The session is committed or rolled back by get_db_session — not here.
Use cases receive repository instances bound to that request's session.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from forenchain.application.ports.audit_repository import AuditRepository
from forenchain.application.ports.custody_repository import CustodyRepository
from forenchain.application.ports.evidence_repository import EvidenceRepository
from forenchain.application.ports.user_repository import UserRepository
from forenchain.application.use_cases.auth.login import (
    LoginUseCase,
    PasswordHandler,
    TOTPHandler,
    TokenHandler,
)
from forenchain.application.use_cases.custody.transfer_custody import TransferCustodyUseCase
from forenchain.application.use_cases.evidence.create_evidence import CreateEvidenceUseCase
from forenchain.application.use_cases.evidence.get_evidence import GetEvidenceUseCase
from forenchain.infrastructure.auth import jwt_handler, password_handler, totp_handler
from forenchain.infrastructure.database.repositories import (
    PostgresAuditRepository,
    PostgresCustodyRepository,
    PostgresEvidenceRepository,
    PostgresUserRepository,
)
from forenchain.infrastructure.database.session import get_db_session


# -----------------------------------------------------------------------
# Handler adapters — wrap module-level functions as Protocol-compliant objects.
# These are request-agnostic singletons; no session needed.
# -----------------------------------------------------------------------

class _PasswordHandlerAdapter:
    def verify(self, plain: str, hashed: str) -> bool:
        return password_handler.verify(plain, hashed)


class _TOTPHandlerAdapter:
    def verify(self, secret: str, code: str) -> bool:
        return totp_handler.verify(secret, code)


class _TokenHandlerAdapter:
    def create_access_token(self, badge_id: str, role: str, agency: str) -> tuple[str, str]:
        return jwt_handler.create_access_token(badge_id, role, agency)


_password_handler = _PasswordHandlerAdapter()
_totp_handler = _TOTPHandlerAdapter()
_token_handler = _TokenHandlerAdapter()


# -----------------------------------------------------------------------
# Repository providers — one instance per request session
# -----------------------------------------------------------------------

def get_evidence_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> EvidenceRepository:
    return PostgresEvidenceRepository(session)


def get_audit_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AuditRepository:
    return PostgresAuditRepository(session)


def get_custody_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> CustodyRepository:
    return PostgresCustodyRepository(session)


def get_user_repo(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> UserRepository:
    return PostgresUserRepository(session)


# -----------------------------------------------------------------------
# Use case providers
# -----------------------------------------------------------------------

def get_create_evidence_use_case(
    evidence_repo: Annotated[EvidenceRepository, Depends(get_evidence_repo)],
    audit_repo: Annotated[AuditRepository, Depends(get_audit_repo)],
) -> CreateEvidenceUseCase:
    return CreateEvidenceUseCase(evidence_repo=evidence_repo, audit_repo=audit_repo)


def get_get_evidence_use_case(
    evidence_repo: Annotated[EvidenceRepository, Depends(get_evidence_repo)],
    audit_repo: Annotated[AuditRepository, Depends(get_audit_repo)],
) -> GetEvidenceUseCase:
    return GetEvidenceUseCase(evidence_repo=evidence_repo, audit_repo=audit_repo)


def get_transfer_custody_use_case(
    evidence_repo: Annotated[EvidenceRepository, Depends(get_evidence_repo)],
    custody_repo: Annotated[CustodyRepository, Depends(get_custody_repo)],
    audit_repo: Annotated[AuditRepository, Depends(get_audit_repo)],
) -> TransferCustodyUseCase:
    return TransferCustodyUseCase(
        evidence_repo=evidence_repo,
        custody_repo=custody_repo,
        audit_repo=audit_repo,
    )


def get_login_use_case(
    user_repo: Annotated[UserRepository, Depends(get_user_repo)],
    audit_repo: Annotated[AuditRepository, Depends(get_audit_repo)],
) -> LoginUseCase:
    return LoginUseCase(
        user_repo=user_repo,
        audit_repo=audit_repo,
        password_handler=_password_handler,
        totp_handler=_totp_handler,
        token_handler=_token_handler,
    )
