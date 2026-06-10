"""
Evidence integrity hashing.

All hash operations are performed server-side. Client-provided hashes are
never used as a source of truth — only for comparison after server recomputation.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime


def _canonical_evidence_string(
    case_id: str,
    fir_number: str,
    description: str,
    evidence_type: str,
    collected_by_badge: str,
    collected_at: datetime,
    collection_location: str,
) -> str:
    """
    Produce a deterministic string from evidence fields.

    Field order and serialisation format are fixed. Changing this function
    invalidates all existing hashes — do not change without a migration plan.
    """
    data = {
        "case_id": case_id,
        "fir_number": fir_number,
        "description": description,
        "evidence_type": evidence_type,
        "collected_by_badge": collected_by_badge,
        "collected_at": collected_at.isoformat(),
        "collection_location": collection_location,
    }
    # sort_keys ensures determinism regardless of insertion order
    return json.dumps(data, sort_keys=True, ensure_ascii=True)


def hash_evidence_descriptor(
    case_id: str,
    fir_number: str,
    description: str,
    evidence_type: str,
    collected_by_badge: str,
    collected_at: datetime,
    collection_location: str,
) -> str:
    """Return the SHA-256 hex digest of the evidence descriptor fields."""
    canonical = _canonical_evidence_string(
        case_id, fir_number, description, evidence_type,
        collected_by_badge, collected_at, collection_location,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_evidence_hash(
    stored_hash: str,
    case_id: str,
    fir_number: str,
    description: str,
    evidence_type: str,
    collected_by_badge: str,
    collected_at: datetime,
    collection_location: str,
) -> bool:
    """
    Recompute the hash from evidence fields and compare to the stored value.

    Uses hmac.compare_digest to prevent timing attacks.
    """
    expected = hash_evidence_descriptor(
        case_id, fir_number, description, evidence_type,
        collected_by_badge, collected_at, collection_location,
    )
    return hmac.compare_digest(stored_hash.lower(), expected.lower())


def compute_hmac(data: str, secret: str) -> str:
    """Compute HMAC-SHA256 of data using the provided secret."""
    return hmac.new(
        secret.encode("utf-8"),
        data.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def hash_transfer(
    evidence_id: str,
    from_badge: str,
    to_badge: str,
    transferred_at: datetime,
    reason: str,
) -> str:
    """Return the SHA-256 hash of a custody transfer record."""
    data = json.dumps({
        "evidence_id": evidence_id,
        "from_badge": from_badge,
        "to_badge": to_badge,
        "transferred_at": transferred_at.isoformat(),
        "reason": reason,
    }, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()
