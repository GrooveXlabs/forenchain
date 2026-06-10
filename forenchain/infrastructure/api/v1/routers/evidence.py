from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from forenchain.application.use_cases.evidence.create_evidence import CreateEvidenceUseCase
from forenchain.application.use_cases.evidence.get_evidence import (
    EvidenceNotFoundError,
    GetEvidenceUseCase,
    IntegrityViolationError,
)
from forenchain.domain.models.evidence import EvidenceCreateRequest
from forenchain.domain.models.user import UserRole
from forenchain.infrastructure.auth.dependencies import TokenData, require_role

router = APIRouter(prefix="/evidence", tags=["evidence"])

_WRITE_ROLES = (UserRole.INVESTIGATOR, UserRole.ADMIN)
_READ_ROLES = (UserRole.INVESTIGATOR, UserRole.FSL_OFFICER, UserRole.FSL_DIRECTOR,
               UserRole.COURT, UserRole.PROSECUTOR, UserRole.SHO, UserRole.ADMIN, UserRole.SSOC)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_evidence(
    body: EvidenceCreateRequest,
    request: Request,
    current_user: Annotated[TokenData, Depends(require_role(*_WRITE_ROLES))],
    use_case: Annotated[CreateEvidenceUseCase, Depends()],
):
    request_id = uuid.UUID(request.state.request_id)
    evidence = await use_case.execute(
        request=body,
        created_by=current_user.badge_id,
        ip_address=request.client.host if request.client else "unknown",
        request_id=request_id,
    )
    return evidence


@router.get("/{evidence_id}", status_code=status.HTTP_200_OK)
async def get_evidence(
    evidence_id: uuid.UUID,
    request: Request,
    current_user: Annotated[TokenData, Depends(require_role(*_READ_ROLES))],
    use_case: Annotated[GetEvidenceUseCase, Depends()],
):
    request_id = uuid.UUID(request.state.request_id)
    try:
        evidence = await use_case.execute(
            evidence_id=evidence_id,
            requested_by=current_user.badge_id,
            ip_address=request.client.host if request.client else "unknown",
            request_id=request_id,
        )
    except EvidenceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="evidence not found")
    except IntegrityViolationError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="evidence integrity check failed — contact system administrator immediately",
        )
    return evidence
