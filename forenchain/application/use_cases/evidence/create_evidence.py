"""
CreateEvidenceUseCase — the highest-risk use case in the system.

Execution order:
1. Write PENDING audit entry — records the intent before anything else executes.
2. Compute hash server-side — client cannot supply or influence this value.
3. Compute HMAC — detects tampering even if the hash algorithm is known.
4. Build QR code data — encodes evidence ID and hash prefix for field scanning.
5. Persist the immutable evidence record.
6. Write SUCCESS audit entry.

If step 2–5 fails, a FAILURE audit entry is written and the exception propagates.
The PENDING entry from step 1 always exists — no attempted creation goes unrecorded.
"""

from __future__ import annotations

import uuid

from forenchain.application.ports.audit_repository import AuditRepository
from forenchain.application.ports.evidence_repository import EvidenceRepository
from forenchain.application.services.audit_service import write_audit
from forenchain.application.services.hash_service import (
    compute_evidence_hash,
    compute_evidence_hmac,
)
from forenchain.domain.models.audit import AuditAction, AuditOutcome
from forenchain.domain.models.evidence import Evidence, EvidenceCreateRequest


class CreateEvidenceUseCase:
    def __init__(
        self,
        evidence_repo: EvidenceRepository,
        audit_repo: AuditRepository,
    ) -> None:
        self._evidence_repo = evidence_repo
        self._audit_repo = audit_repo

    async def execute(
        self,
        request: EvidenceCreateRequest,
        created_by: str,    # badge_id from JWT
        agency: str,        # agency from JWT — used for Row-Level Security
        ip_address: str,
        request_id: uuid.UUID,
    ) -> Evidence:
        entity_id = uuid.uuid4()

        await write_audit(
            audit_repo=self._audit_repo,
            action=AuditAction.EVIDENCE_CREATED,
            performed_by=created_by,
            ip_address=ip_address,
            entity_type="evidence",
            outcome=AuditOutcome.PENDING,
            entity_id=entity_id,
            details={"case_id": request.case_id, "fir_number": request.fir_number},
            request_id=request_id,
        )

        try:
            hash_sha256 = compute_evidence_hash(
                case_id=request.case_id,
                fir_number=request.fir_number,
                description=request.description,
                evidence_type=request.evidence_type.value,
                collected_by_badge=request.collected_by_badge,
                collected_at=request.collected_at,
                collection_location=request.collection_location,
            )

            hmac_signature = compute_evidence_hmac(hash_sha256)
            qr_code_data = f"FORENCHAIN:{entity_id}:{hash_sha256[:16]}"

            evidence = Evidence(
                id=entity_id,
                case_id=request.case_id,
                fir_number=request.fir_number,
                description=request.description,
                evidence_type=request.evidence_type,
                collected_by_badge=request.collected_by_badge,
                collected_at=request.collected_at,
                collection_location=request.collection_location,
                hash_sha256=hash_sha256,
                hmac_signature=hmac_signature,
                qr_code_data=qr_code_data,
            )

            saved = await self._evidence_repo.create(evidence, agency=agency, created_by=created_by)

            await write_audit(
                audit_repo=self._audit_repo,
                action=AuditAction.EVIDENCE_CREATED,
                performed_by=created_by,
                ip_address=ip_address,
                entity_type="evidence",
                outcome=AuditOutcome.SUCCESS,
                entity_id=entity_id,
                request_id=request_id,
            )

            return saved

        except Exception as exc:
            await write_audit(
                audit_repo=self._audit_repo,
                action=AuditAction.EVIDENCE_CREATED,
                performed_by=created_by,
                ip_address=ip_address,
                entity_type="evidence",
                outcome=AuditOutcome.FAILURE,
                entity_id=entity_id,
                details={"error": str(exc)},
                request_id=request_id,
            )
            raise
