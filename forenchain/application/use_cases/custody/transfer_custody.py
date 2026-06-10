"""
TransferCustodyUseCase — appends a transfer to the chain.

from_badge is read from the JWT (the authenticated officer), NOT from the request.
An officer cannot claim to transfer from a badge they are not authenticated as.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from forenchain.application.ports.audit_repository import AuditRepository
from forenchain.application.ports.custody_repository import CustodyRepository
from forenchain.application.ports.evidence_repository import EvidenceRepository
from forenchain.application.services.audit_service import write_audit
from forenchain.application.services.hash_service import compute_transfer_hash
from forenchain.domain.models.audit import AuditAction, AuditOutcome
from forenchain.domain.models.custody import CustodyTransfer, CustodyTransferRequest


class EvidenceNotFoundError(Exception):
    pass


class TransferCustodyUseCase:
    def __init__(
        self,
        evidence_repo: EvidenceRepository,
        custody_repo: CustodyRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self._evidence_repo = evidence_repo
        self._custody_repo = custody_repo
        self._audit_repo = audit_repo

    async def execute(
        self,
        request: CustodyTransferRequest,
        from_badge: str,       # from JWT — never from request body
        from_location: str,    # from JWT or last custody record
        ip_address: str,
        request_id: uuid.UUID,
    ) -> CustodyTransfer:
        evidence = await self._evidence_repo.get_by_id(request.evidence_id)
        if evidence is None:
            raise EvidenceNotFoundError(f"Evidence {request.evidence_id} not found")

        transfer_id = uuid.uuid4()
        transferred_at = datetime.now(timezone.utc)

        # Audit BEFORE the transfer is written.
        await write_audit(
            audit_repo=self._audit_repo,
            action=AuditAction.CUSTODY_TRANSFERRED,
            performed_by=from_badge,
            ip_address=ip_address,
            entity_type="custody_transfer",
            outcome=AuditOutcome.PENDING,
            entity_id=transfer_id,
            details={
                "evidence_id": str(request.evidence_id),
                "from_badge": from_badge,
                "to_badge": request.to_badge,
            },
            request_id=request_id,
        )

        try:
            transfer_hash = compute_transfer_hash(
                evidence_id=str(request.evidence_id),
                from_badge=from_badge,
                to_badge=request.to_badge,
                transferred_at=transferred_at,
                reason=request.reason,
            )

            transfer = CustodyTransfer(
                id=transfer_id,
                evidence_id=request.evidence_id,
                from_badge=from_badge,
                to_badge=request.to_badge,
                from_location=from_location,
                to_location=request.to_location,
                transferred_at=transferred_at,
                reason=request.reason,
                transfer_hash=transfer_hash,
            )

            saved = await self._custody_repo.append(transfer)

            await write_audit(
                audit_repo=self._audit_repo,
                action=AuditAction.CUSTODY_TRANSFERRED,
                performed_by=from_badge,
                ip_address=ip_address,
                entity_type="custody_transfer",
                outcome=AuditOutcome.SUCCESS,
                entity_id=transfer_id,
                request_id=request_id,
            )

            return saved

        except Exception as exc:
            await write_audit(
                audit_repo=self._audit_repo,
                action=AuditAction.CUSTODY_TRANSFERRED,
                performed_by=from_badge,
                ip_address=ip_address,
                entity_type="custody_transfer",
                outcome=AuditOutcome.FAILURE,
                entity_id=transfer_id,
                details={"error": str(exc)},
                request_id=request_id,
            )
            raise
