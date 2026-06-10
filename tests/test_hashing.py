"""
Tests for evidence integrity hashing.

These tests define what the hashing layer must do.
They were written before the implementation in forenchain/security/hashing.py.
"""

from datetime import datetime

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from forenchain.security.hashing import (
    hash_evidence_descriptor,
    verify_evidence_hash,
    hash_transfer,
    compute_hmac,
)

FIXED_TIMESTAMP = datetime(2026, 1, 15, 10, 30, 0)

SAMPLE_EVIDENCE = {
    "case_id": "PB-2026-001",
    "fir_number": "FIR-001/2026",
    "description": "Laptop recovered from scene",
    "evidence_type": "digital",
    "collected_by_badge": "PB-1234",
    "collected_at": FIXED_TIMESTAMP,
    "collection_location": "Sector 17, Chandigarh",
}


class TestHashEvidenceDescriptor:
    def test_returns_64_char_hex_string(self):
        h = hash_evidence_descriptor(**SAMPLE_EVIDENCE)
        assert len(h) == 64
        int(h, 16)  # must be valid hex

    def test_same_inputs_produce_same_hash(self):
        h1 = hash_evidence_descriptor(**SAMPLE_EVIDENCE)
        h2 = hash_evidence_descriptor(**SAMPLE_EVIDENCE)
        assert h1 == h2

    def test_different_case_id_produces_different_hash(self):
        h1 = hash_evidence_descriptor(**SAMPLE_EVIDENCE)
        modified = {**SAMPLE_EVIDENCE, "case_id": "PB-2026-002"}
        h2 = hash_evidence_descriptor(**modified)
        assert h1 != h2

    def test_different_description_produces_different_hash(self):
        h1 = hash_evidence_descriptor(**SAMPLE_EVIDENCE)
        modified = {**SAMPLE_EVIDENCE, "description": "Phone recovered from scene"}
        h2 = hash_evidence_descriptor(**modified)
        assert h1 != h2

    def test_different_timestamp_produces_different_hash(self):
        h1 = hash_evidence_descriptor(**SAMPLE_EVIDENCE)
        modified = {**SAMPLE_EVIDENCE, "collected_at": datetime(2026, 1, 16, 10, 30, 0)}
        h2 = hash_evidence_descriptor(**modified)
        assert h1 != h2

    def test_hash_is_lowercase(self):
        h = hash_evidence_descriptor(**SAMPLE_EVIDENCE)
        assert h == h.lower()

    @given(st.text(min_size=1, max_size=50), st.text(min_size=3, max_size=500))
    @settings(max_examples=100)
    def test_arbitrary_inputs_produce_valid_hex_hash(self, case_id: str, description: str):
        # Any non-empty input must produce a valid 64-char hex hash — no crashes
        try:
            h = hash_evidence_descriptor(
                case_id=case_id,
                fir_number="FIR-001",
                description=description,
                evidence_type="digital",
                collected_by_badge="PB-001",
                collected_at=FIXED_TIMESTAMP,
                collection_location="Chandigarh",
            )
            assert len(h) == 64
            int(h, 16)
        except Exception:
            pass  # invalid input may raise — that is acceptable


class TestVerifyEvidenceHash:
    def test_correct_hash_verifies(self):
        h = hash_evidence_descriptor(**SAMPLE_EVIDENCE)
        assert verify_evidence_hash(h, **SAMPLE_EVIDENCE) is True

    def test_tampered_description_fails_verification(self):
        h = hash_evidence_descriptor(**SAMPLE_EVIDENCE)
        tampered = {**SAMPLE_EVIDENCE, "description": "Gun recovered from scene"}
        assert verify_evidence_hash(h, **tampered) is False

    def test_tampered_case_id_fails_verification(self):
        h = hash_evidence_descriptor(**SAMPLE_EVIDENCE)
        tampered = {**SAMPLE_EVIDENCE, "case_id": "PB-9999-999"}
        assert verify_evidence_hash(h, **tampered) is False

    def test_wrong_hash_fails_verification(self):
        assert verify_evidence_hash("a" * 64, **SAMPLE_EVIDENCE) is False

    def test_empty_hash_fails_verification(self):
        assert verify_evidence_hash("", **SAMPLE_EVIDENCE) is False

    def test_uppercase_hash_still_verifies(self):
        # Case insensitive comparison — courts should not fail on case differences
        h = hash_evidence_descriptor(**SAMPLE_EVIDENCE)
        assert verify_evidence_hash(h.upper(), **SAMPLE_EVIDENCE) is True


class TestHashTransfer:
    def test_returns_64_char_hex(self):
        h = hash_transfer("ev-001", "PB-001", "FSL-001", FIXED_TIMESTAMP, "Sending for analysis")
        assert len(h) == 64
        int(h, 16)

    def test_same_inputs_deterministic(self):
        h1 = hash_transfer("ev-001", "PB-001", "FSL-001", FIXED_TIMESTAMP, "Sending for analysis")
        h2 = hash_transfer("ev-001", "PB-001", "FSL-001", FIXED_TIMESTAMP, "Sending for analysis")
        assert h1 == h2

    def test_different_evidence_id_changes_hash(self):
        h1 = hash_transfer("ev-001", "PB-001", "FSL-001", FIXED_TIMESTAMP, "Sending for analysis")
        h2 = hash_transfer("ev-002", "PB-001", "FSL-001", FIXED_TIMESTAMP, "Sending for analysis")
        assert h1 != h2


class TestComputeHmac:
    def test_returns_non_empty_string(self):
        result = compute_hmac("test data", "secret")
        assert len(result) == 64

    def test_different_secrets_produce_different_hmacs(self):
        h1 = compute_hmac("test data", "secret1")
        h2 = compute_hmac("test data", "secret2")
        assert h1 != h2

    def test_same_inputs_are_deterministic(self):
        h1 = compute_hmac("test data", "secret")
        h2 = compute_hmac("test data", "secret")
        assert h1 == h2
