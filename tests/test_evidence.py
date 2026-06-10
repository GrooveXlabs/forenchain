"""
Tests for the Evidence model and its validation rules.

Written before the implementation to define what Evidence must enforce.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from forenchain.models.evidence import Evidence, EvidenceStatus, EvidenceType, EvidenceCreateRequest

VALID_HASH = "a" * 64
FIXED_TIME = datetime(2026, 1, 15, 10, 30, 0)


def make_evidence(**overrides: object) -> dict:
    base = {
        "case_id": "PB-2026-001",
        "fir_number": "FIR-001/2026",
        "description": "Laptop recovered from scene",
        "evidence_type": EvidenceType.DIGITAL,
        "collected_by_badge": "PB-1234",
        "collected_at": FIXED_TIME,
        "collection_location": "Sector 17, Chandigarh",
        "hash_sha256": VALID_HASH,
        "hmac_signature": "b" * 64,
    }
    base.update(overrides)
    return base


class TestEvidenceCreation:
    def test_valid_evidence_creates_successfully(self):
        e = Evidence(**make_evidence())
        assert e.case_id == "PB-2026-001"
        assert e.status == EvidenceStatus.COLLECTED

    def test_default_status_is_collected(self):
        e = Evidence(**make_evidence())
        assert e.status == EvidenceStatus.COLLECTED

    def test_id_is_assigned_automatically(self):
        e = Evidence(**make_evidence())
        assert e.id is not None

    def test_two_instances_have_different_ids(self):
        e1 = Evidence(**make_evidence())
        e2 = Evidence(**make_evidence())
        assert e1.id != e2.id


class TestEvidenceImmutability:
    def test_evidence_is_frozen(self):
        e = Evidence(**make_evidence())
        with pytest.raises(Exception):
            e.description = "modified"  # type: ignore[misc]

    def test_hash_cannot_be_changed_after_creation(self):
        e = Evidence(**make_evidence())
        with pytest.raises(Exception):
            e.hash_sha256 = "b" * 64  # type: ignore[misc]


class TestEvidenceHashValidation:
    def test_hash_must_be_64_chars(self):
        with pytest.raises(ValidationError):
            Evidence(**make_evidence(hash_sha256="abc"))

    def test_hash_must_be_valid_hex(self):
        with pytest.raises(ValidationError):
            Evidence(**make_evidence(hash_sha256="z" * 64))

    def test_hash_is_stored_lowercase(self):
        e = Evidence(**make_evidence(hash_sha256="A" * 64))
        assert e.hash_sha256 == "a" * 64


class TestEvidenceFieldValidation:
    def test_empty_case_id_rejected(self):
        with pytest.raises(ValidationError):
            Evidence(**make_evidence(case_id=""))

    def test_case_id_with_sql_injection_rejected(self):
        with pytest.raises(ValidationError):
            Evidence(**make_evidence(case_id="1'; DROP TABLE evidence; --"))

    def test_case_id_with_xss_rejected(self):
        with pytest.raises(ValidationError):
            Evidence(**make_evidence(case_id="<script>alert(1)</script>"))

    def test_too_short_description_rejected(self):
        with pytest.raises(ValidationError):
            Evidence(**make_evidence(description="ab"))

    def test_case_id_allows_valid_characters(self):
        e = Evidence(**make_evidence(case_id="PB-2026/001_A"))
        assert e.case_id == "PB-2026/001_A"


class TestEvidenceCreateRequest:
    def test_create_request_does_not_accept_hash(self):
        # Officers cannot supply their own hash — it must be computed server-side
        fields = {
            "case_id": "PB-2026-001",
            "fir_number": "FIR-001/2026",
            "description": "Laptop recovered",
            "evidence_type": EvidenceType.DIGITAL,
            "collected_by_badge": "PB-1234",
            "collected_at": FIXED_TIME,
            "collection_location": "Chandigarh",
        }
        req = EvidenceCreateRequest(**fields)
        assert not hasattr(req, "hash_sha256")

    def test_create_request_with_injection_in_case_id_rejected(self):
        with pytest.raises(ValidationError):
            EvidenceCreateRequest(
                case_id="'; DROP TABLE evidence; --",
                fir_number="FIR-001",
                description="Test",
                evidence_type=EvidenceType.DIGITAL,
                collected_by_badge="PB-001",
                collected_at=FIXED_TIME,
                collection_location="Chandigarh",
            )
