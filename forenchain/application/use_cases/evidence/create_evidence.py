"""
CreateEvidenceUseCase — the highest-risk use case in the system.

Responsibilities (in order):
1. Write audit log entry BEFORE anything else executes
2. Compute hash server-side from request fields — never from client input
3. Compute HMAC over the hash — detects tampering even if hash algorithm is known
4. Generate QR code data
5. Persist the evidence record
6. Write success audit log entry

If any step from 2 onward fails, a failure audit entry is written and the exception propagates.
The initial audit entry (step 1) ensures even a failed creation attempt is recorded.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from forenchain.application.ports.audit_repository import AuditRepository
from forenchain.application.ports.evidence_repository import EvidenceRepository
from forenchain.application.services.audit_service import write_audit
from forenchain.application.services.hash_service import (
    compute_evidence_hash,
    compute_evidence_hmac,
)
from forenchain.domain.models.audit import AuditAction
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
        created_by: str,   # badge_id from JWT — not from request body
        ip_address: str,
        request_id: uuid.UUID,
    ) -> Evidence:
        entity_id = uuid.uuid4()

        # Step 1: Write intent to audit log before anything executes.
        # Even if the next steps fail, this entry records the attempt.
        await write_audit(
            audit_repo=self._audit_repo,
            action=AuditAction.EVIDENCE_CREATED,
            performed_by=created_by,
            ip_address=ip_address,
            entity_type="evidence",
            outcome="pending",
            entity_id=entity_id,
            details={"case_id": request.case_id, "fir_number": request.fir_number},
            request_id=request_id,
        )

        try:
            # Step 2: Hash computed server-side. Client cannot influence this value.
            hash_sha256 = compute_evidence_hash(
                case_id=request.case_id,
                fir_number=request.fir_number,
                description=request.description,
                evidence_type=request.evidence_type.value,
                collected_by_badge=request.collected_by_badge,
                collected_at=request.collected_at,
                collection_location=request.collection_location,
            )

            # Step 3: HMAC over the hash using server-side secret.
            hmac_signature = compute_evidence_hmac(hash_sha256)

            # Step 4: QR code data — encodes the evidence ID and hash for field scanning.
            qr_code_data = f"FORENCHAIN:{entity_id}:{hash_sha256[:16]}"

            # Step 5: Build the immutable domain model.
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

            # Step 6: Persist.
            saved = await self._evidence_repo.create(evidence)

            # Step 7: Success audit.
            await write_audit(
                audit_repo=self._audit_repo,
                action=AuditAction.EVIDENCE_CREATED,
                performed_by=created_by,
                ip_address=ip_address,
                entity_type="evidence",
                outcome="success",
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
                outcome="failure",
                entity_id=entity_id,
                details={"error": str(exc)},
                request_id=request_id,
            )
            raise
