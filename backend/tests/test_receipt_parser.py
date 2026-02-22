"""Tests for receipt parser. With NOVA_MODE=mock, parse_receipt returns fixed dict."""
import pytest

from app.services.receipt_parser import parse_receipt


class TestParseReceiptMock:
    """When settings.nova_mode is mock, parse_receipt returns fixed demo dict."""

    def test_mock_returns_expected_keys(self):
        out = parse_receipt(b"fake-image-bytes", "image/png")
        assert "amount" in out
        assert "merchant" in out
        assert "date" in out
        assert "category" in out
        assert "currency" in out
        assert "confidence" in out

    def test_mock_amount_and_merchant(self):
        out = parse_receipt(b"any", "image/jpeg")
        assert out["amount"] == "45.50"
        assert out["merchant"] == "Demo Cafe"
        assert out["confidence"] == 0.95
