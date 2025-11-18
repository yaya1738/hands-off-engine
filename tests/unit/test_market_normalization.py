"""Test market normalization to Market dataclass"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "termux-hands-off" / "agent"))

from polymarket_skeleton import to_market, Market, Category
import pytest


@pytest.mark.unit
class TestMarketNormalization:
    """Test suite for to_market() function"""

    def test_standard_market_normalization(self):
        """Standard Polymarket JSON should normalize correctly"""
        raw = {
            "id": "test-001",
            "question": "Test question?",
            "yes_price": 0.55,
            "no_price": 0.45,
            "closes_at": "2025-12-31T23:59:59Z",
            "volume": 100000
        }

        market = to_market(raw)

        assert market.id == "test-001"
        assert market.question == "Test question?"
        assert market.yes_price == 0.55
        assert market.no_price == 0.45
        assert market.closes_at == "2025-12-31T23:59:59Z"
        assert market.volume == 100000
        assert isinstance(market.category, Category)

    def test_alternative_field_names(self):
        """Should handle _id, title, best_yes, end_date alternatives"""
        raw = {
            "_id": "alt-001",
            "title": "Alternative naming",
            "best_yes": 0.6,
            "best_no": 0.4,
            "end_date": "2025-12-31"
        }

        market = to_market(raw)

        assert market.id == "alt-001"
        assert market.question == "Alternative naming"
        assert market.yes_price == 0.6
        assert market.no_price == 0.4
        assert market.closes_at == "2025-12-31"

    def test_slug_as_id_fallback(self):
        """Should use 'slug' if 'id' and '_id' are missing"""
        raw = {
            "slug": "slug-001",
            "question": "Has slug",
            "yes_price": 0.5,
            "no_price": 0.5
        }

        market = to_market(raw)
        assert market.id == "slug-001"

    def test_missing_optional_fields(self):
        """Missing volume/tags should not crash"""
        raw = {
            "id": "minimal",
            "question": "Minimal market",
            "yes_price": 0.5,
            "no_price": 0.5
        }

        market = to_market(raw)

        assert market.id == "minimal"
        assert market.volume is None  # Should be None, not crash
        assert market.question == "Minimal market"

    def test_extra_fields_preserved(self):
        """Extra fields should be stored in extra dict"""
        raw = {
            "id": "extra-001",
            "question": "Test",
            "yes_price": 0.5,
            "no_price": 0.5,
            "custom_field": "custom_value",
            "metadata": {"key": "value"}
        }

        market = to_market(raw)

        assert "custom_field" in market.extra
        assert market.extra["custom_field"] == "custom_value"
        assert "metadata" in market.extra
        assert market.extra["metadata"] == {"key": "value"}

    def test_price_types_are_float(self):
        """Prices should always be float"""
        raw = {
            "id": "test",
            "question": "Test",
            "yes_price": "0.55",  # String
            "no_price": "0.45"
        }

        market = to_market(raw)

        assert isinstance(market.yes_price, float)
        assert isinstance(market.no_price, float)
        assert market.yes_price == 0.55
        assert market.no_price == 0.45

    def test_missing_price_defaults_to_half(self):
        """Missing price fields should default to 0.5"""
        raw = {
            "id": "no-prices",
            "question": "No prices"
        }

        market = to_market(raw)

        # Should use default of 0.5
        assert market.yes_price == 0.5
        assert market.no_price == 0.5

    def test_category_inference_applied(self):
        """Category should be inferred if not provided"""
        raw = {
            "id": "crypto-market",
            "question": "Will Bitcoin reach $100k?",
            "yes_price": 0.6,
            "no_price": 0.4
        }

        market = to_market(raw)
        assert market.category == Category.CRYPTO

    def test_explicit_category_used(self):
        """Explicit category should override inference"""
        raw = {
            "id": "explicit-cat",
            "question": "Will Bitcoin reach $100k?",  # Would infer CRYPTO
            "category": "other",  # But explicitly set to OTHER
            "yes_price": 0.5,
            "no_price": 0.5
        }

        market = to_market(raw)
        assert market.category == Category.OTHER

    def test_invalid_category_falls_back_to_inference(self):
        """Invalid explicit category should fall back to inference"""
        raw = {
            "id": "invalid-cat",
            "question": "Will Bitcoin reach $100k?",
            "category": "invalid_category",  # Not a valid Category value
            "yes_price": 0.5,
            "no_price": 0.5
        }

        market = to_market(raw)
        # Should fall back to inference and get CRYPTO
        assert market.category == Category.CRYPTO

    def test_volume_none_when_missing(self):
        """Volume should be None (not 0.0) when missing"""
        raw = {
            "id": "no-volume",
            "question": "Test",
            "yes_price": 0.5,
            "no_price": 0.5
        }

        market = to_market(raw)
        assert market.volume is None

    def test_volume_float_conversion(self):
        """Volume should be converted to float when present"""
        raw = {
            "id": "str-volume",
            "question": "Test",
            "yes_price": 0.5,
            "no_price": 0.5,
            "volume": "100000"
        }

        market = to_market(raw)
        assert isinstance(market.volume, float)
        assert market.volume == 100000.0
