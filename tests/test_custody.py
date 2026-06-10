"""
Tests for the CustodyTransfer model.

The chain of custody is append-only and immutable.
These tests define what must never be possible.
"""

import uuid
from datetime import datetime

import pytest
from pydantic import ValidationError

from forenchain.models.custody import CustodyTransfer, CustodyTransferRequest

FIXED_TIME = datetime(2026, 1, 15, 10, 30, 0)
EVIDENCE_ID = uuid.uuid4()


def make_transfer(**overrides: object) -> dict:
    base = {
        "evidence_id": EVIDENCE_ID,
        "from_badge": "PB-1234",
        "to_badge": "FSL-001",
        "from_location": "Police Station Sector 17",
        "to_location": "FSL Chandigarh",
        "transferred_at": FIXED_TIME,
        "reason": "Sending for digital forensic examination",
        "transfer_hash": "c" * 64,
    }
    base.update(overrides)
    return base


class TestCustodyTransferCreation:
    def test_valid_transfer_creates_successfully(self):
        t = CustodyTransfer(**make_transfer())
        assert t.from_badge == "PB-1234"
        assert t.to_badge == "FSL-001"

    def test_id_is_auto_assigned(self):
        t = CustodyTransfer(**make_transfer())
        assert t.id is not None

    def test_two_transfers_have_different_ids(self):
        t1 = CustodyTransfer(**make_transfer())
        t2 = CustodyTransfer(**make_transfer())
        assert t1.id != t2.id


class TestCustodyTransferImmutability:
    def test_transfer_is_frozen(self):
        t = CustodyTransfer(**make_transfer())
        with pytest.raises(Exception):
            t.reason = "modified reason"  # type: ignore[misc]

    def test_from_badge_cannot_be_changed(self):
        t = CustodyTransfer(**make_transfer())
        with pytest.raises(Exception):
            t.from_badge = "ATTACKER-001"  # type: ignore[misc]


class TestCustodyTransferValidation:
    def test_same_from_and_to_badge_rejected(self):
        # An officer cannot transfer evidence to themselves
        with pytest.raises(ValidationError):
            CustodyTransfer(**make_transfer(from_badge="PB-1234", to_badge="PB-1234"))

    def test_empty_reason_rejected(self):
        with pytest.raises(ValidationError):
            CustodyTransfer(**make_transfer(reason="ab"))

    def test_empty_from_badge_rejected(self):
        with pytest.raises(ValidationError):
            CustodyTransfer(**make_transfer(from_badge=""))

    def test_empty_to_badge_rejected(self):
        with pytest.raises(ValidationError):
            CustodyTransfer(**make_transfer(to_badge=""))


class TestCustodyTransferRequest:
    def test_request_does_not_contain_hash(self):
        # Officers cannot supply a transfer hash — computed server-side
        req = CustodyTransferRequest(
            evidence_id=EVIDENCE_ID,
            to_badge="FSL-001",
            to_location="FSL Chandigarh",
            reason="Sending for analysis",
        )
        assert not hasattr(req, "transfer_hash")
        assert not hasattr(req, "from_badge")  # derived from authenticated user
