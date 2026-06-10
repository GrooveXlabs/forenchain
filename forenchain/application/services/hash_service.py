"""
Wraps domain hashing functions with the HMAC_SECRET injected from config.

The domain layer never touches config. This service is the bridge.
"""

from __future__ import annotations

from datetime import datetime

from forenchain.config import get_settings
from forenchain.domain.security.hashing import (
    compute_hmac,
    hash_evidence_descriptor,
    hash_transfer,
    verify_evidence_hash,
)


def compute_evidence_hash(
    case_id: str,
    fir_number: str,
    description: str,
    evidence_type: str,
    collected_by_badge: str,
    collected_at: datetime,
    collection_location: str,
) -> str:
    return hash_evidence_descriptor(
        case_id=case_id,
        fir_number=fir_number,
        description=description,
        evidence_type=evidence_type,
        collected_by_badge=collected_by_badge,
        collected_at=collected_at,
        collection_location=collection_location,
    )


def compute_evidence_hmac(hash_sha256: str) -> str:
    settings = get_settings()
    return compute_hmac(hash_sha256, settings.hmac_secret)


def compute_transfer_hash(
    evidence_id: str,
    from_badge: str,
    to_badge: str,
    transferred_at: datetime,
    reason: str,
) -> str:
    return hash_transfer(
        evidence_id=evidence_id,
        from_badge=from_badge,
        to_badge=to_badge,
        transferred_at=transferred_at,
        reason=reason,
    )


def verify_integrity(
    stored_hash: str,
    case_id: str,
    fir_number: str,
    description: str,
    evidence_type: str,
    collected_by_badge: str,
    collected_at: datetime,
    collection_location: str,
) -> bool:
    return verify_evidence_hash(
        stored_hash=stored_hash,
        case_id=case_id,
        fir_number=fir_number,
        description=description,
        evidence_type=evidence_type,
        collected_by_badge=collected_by_badge,
        collected_at=collected_at,
        collection_location=collection_location,
    )
