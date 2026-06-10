"""
GetEvidenceUseCase — re-verifies integrity on every read.

Every time evidence is fetched, the hash is recomputed and compared to the stored value.
A mismatch means the record was tampered with — either via a bug or a direct DB attack.
The read is blocked and a critical audit entry is written.
"""

from __future__ import annotations

import uuid

from forenchain.application.ports.audit_repository import AuditRepository
from forenchain.application.ports.evidence_repository import EvidenceRepository
from forenchain.application.services.audit_service import write_audit
from forenchain.application.services.hash_service import verify_integrity
from forenchain.domain.models.audit import AuditAction
from forenchain.domain.models.evidence import Evidence


class IntegrityViolationError(Exception):
    """Raised when a stored evidence hash does not match its recomputed value."""


class EvidenceNotFoundError(Exception):
    pass


class GetEvidenceUseCase:
    def __init__(
        self,
        evidence_repo: EvidenceRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self._evidence_repo = evidence_repo
        self._audit_repo = audit_repo

    async def execute(
        self,
        evidence_id: uuid.UUID,
        requested_by: str,
        ip_address: str,
        request_id: uuid.UUID,
    ) -> Evidence:
        evidence = await self._evidence_repo.get_by_id(evidence_id)

        if evidence is None:
            raise EvidenceNotFoundError(f"Evidence {evidence_id} not found")

        # Re-verify integrity on every read.
        is_valid = verify_integrity(
            stored_hash=evidence.hash_sha256,
            case_id=evidence.case_id,
            fir_number=evidence.fir_number,
            description=evidence.description,
            evidence_type=evidence.evidence_type.value,
            collected_by_badge=evidence.collected_by_badge,
            collected_at=evidence.collected_at,
            collection_location=evidence.collection_location,
        )

        if not is_valid:
            # This is a critical event — write to audit log immediately.
            await write_audit(
                audit_repo=self._audit_repo,
                action=AuditAction.EVIDENCE_VIEWED,
                performed_by=requested_by,
                ip_address=ip_address,
                entity_type="evidence",
                outcome="failure",
                entity_id=evidence_id,
                details={"reason": "INTEGRITY_VIOLATION", "stored_hash": evidence.hash_sha256},
                request_id=request_id,
            )
            raise IntegrityViolationError(
                f"Evidence {evidence_id} hash mismatch — record may have been tampered with"
            )

        await write_audit(
            audit_repo=self._audit_repo,
            action=AuditAction.EVIDENCE_VIEWED,
            performed_by=requested_by,
            ip_address=ip_address,
            entity_type="evidence",
            outcome="success",
            entity_id=evidence_id,
            request_id=request_id,
        )

        return evidence
