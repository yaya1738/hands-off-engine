"""Unit tests for LLM prompt library"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm.prompt_library import (
    get_base_prompt,
    get_politics_prompt,
    get_crypto_prompt,
    get_sports_prompt,
    get_macro_prompt,
    get_generic_prompt,
    get_prompt_for_market,
    get_prompt_metadata,
    PROMPT_ROUTER,
    PROMPT_VERSION,
)
import pytest
import json


@pytest.mark.unit
class TestPromptLibrary:
    """Test suite for prompt generation and routing"""

    def test_prompt_version_defined(self):
        """Prompt version should be defined"""
        assert PROMPT_VERSION is not None
        assert isinstance(PROMPT_VERSION, str)
        assert PROMPT_VERSION.startswith("v")

    def test_base_prompt_contains_json_schema(self):
        """Base prompt should include JSON output schema"""
        base = get_base_prompt()

        assert "fair_probability" in base
        assert "confidence" in base
        assert "edge_bps" in base
        assert "reasoning" in base
        assert "action" in base

        # Should specify valid values for enums
        assert "low|medium|high" in base
        assert "buy_yes|buy_no|avoid" in base

    def test_base_prompt_includes_calibration_guidance(self):
        """Base prompt should include calibration guidance"""
        base = get_base_prompt()

        assert "calibrated" in base.lower() or "base rate" in base.lower()

    def test_politics_prompt_structure(self):
        """Politics prompt should include base + category-specific guidance"""
        market_data = {
            "question": "Will the Senate pass the bill?",
            "yes_price": 0.65,
            "volume": 100000,
            "closes_at": "2025-03-01",
        }

        prompt = get_politics_prompt(market_data)

        # Should include base schema
        assert "fair_probability" in prompt
        assert "JSON" in prompt

        # Should include category marker
        assert "POLITICS" in prompt.upper()

        # Should include market data
        assert "Will the Senate pass the bill?" in prompt
        assert "65" in prompt  # Price as percentage

        # Should include politics-specific guidance
        assert any(
            keyword in prompt.lower()
            for keyword in ["polling", "electoral", "parliament", "precedent"]
        )

    def test_crypto_prompt_structure(self):
        """Crypto prompt should include crypto-specific guidance"""
        market_data = {
            "question": "Will Bitcoin reach $100k?",
            "yes_price": 0.62,
            "volume": 500000,
            "closes_at": "2025-12-31",
        }

        prompt = get_crypto_prompt(market_data)

        assert "CRYPTO" in prompt.upper()
        assert "Will Bitcoin reach $100k?" in prompt

        # Should include crypto-specific guidance
        assert any(
            keyword in prompt.lower()
            for keyword in ["volatility", "crypto", "regulatory", "technical"]
        )

    def test_sports_prompt_structure(self):
        """Sports prompt should include sports-specific guidance"""
        market_data = {
            "question": "Will Lakers win?",
            "yes_price": 0.55,
            "volume": 75000,
            "closes_at": "2025-06-15",
        }

        prompt = get_sports_prompt(market_data)

        assert "SPORTS" in prompt.upper()
        assert "Will Lakers win?" in prompt

        # Should include sports-specific guidance
        assert any(
            keyword in prompt.lower()
            for keyword in ["performance", "team", "player", "injury", "roster"]
        )

    def test_macro_prompt_structure(self):
        """Macro prompt should include economics-specific guidance"""
        market_data = {
            "question": "Will the Fed raise rates?",
            "yes_price": 0.70,
            "volume": 200000,
            "closes_at": "2025-04-01",
        }

        prompt = get_macro_prompt(market_data)

        assert "MACRO" in prompt.upper()
        assert "Will the Fed raise rates?" in prompt

        # Should include macro-specific guidance
        assert any(
            keyword in prompt.lower()
            for keyword in ["economic", "central bank", "policy", "gdp", "inflation"]
        )

    def test_generic_prompt_structure(self):
        """Generic prompt should work for uncategorized markets"""
        market_data = {
            "question": "Will it rain tomorrow?",
            "yes_price": 0.50,
            "volume": 10000,
            "closes_at": "2025-01-20",
            "category": "weather",
        }

        prompt = get_generic_prompt(market_data)

        assert "Will it rain tomorrow?" in prompt
        assert "WEATHER" in prompt.upper()

        # Should include generic guidance
        assert any(
            keyword in prompt.lower()
            for keyword in ["base rate", "information", "market efficiency"]
        )

    def test_prompt_router_has_all_categories(self):
        """Prompt router should include all expected categories"""
        expected_categories = ["politics", "crypto", "sports", "macro", "other"]

        for category in expected_categories:
            assert category in PROMPT_ROUTER

    def test_get_prompt_for_market_politics(self):
        """Should route politics markets to politics prompt"""
        market_data = {
            "question": "Will the election happen?",
            "category": "politics",
            "yes_price": 0.5,
            "volume": 100000,
            "closes_at": "2025-11-05",
        }

        prompt = get_prompt_for_market(market_data)

        assert "POLITICS" in prompt.upper()
        assert "Will the election happen?" in prompt

    def test_get_prompt_for_market_crypto(self):
        """Should route crypto markets to crypto prompt"""
        market_data = {
            "question": "Will ETH hit $10k?",
            "category": "crypto",
            "yes_price": 0.4,
            "volume": 300000,
            "closes_at": "2025-12-31",
        }

        prompt = get_prompt_for_market(market_data)

        assert "CRYPTO" in prompt.upper()
        assert "Will ETH hit $10k?" in prompt

    def test_get_prompt_for_market_unknown_category(self):
        """Should fall back to generic for unknown categories"""
        market_data = {
            "question": "Random event?",
            "category": "unknown",
            "yes_price": 0.5,
            "volume": 5000,
            "closes_at": "2025-01-01",
        }

        prompt = get_prompt_for_market(market_data)

        # Should use generic prompt
        assert "Random event?" in prompt
        assert "UNKNOWN" in prompt.upper()

    def test_get_prompt_for_market_missing_category(self):
        """Should handle missing category gracefully"""
        market_data = {
            "question": "Event without category",
            "yes_price": 0.5,
            "volume": 1000,
            "closes_at": "2025-01-01",
        }

        prompt = get_prompt_for_market(market_data)

        # Should default to generic
        assert "Event without category" in prompt

    def test_prompt_includes_market_price(self):
        """All prompts should include market price"""
        market_data = {
            "question": "Test market",
            "category": "other",
            "yes_price": 0.73,  # 73%
            "volume": 1000,
            "closes_at": "2025-01-01",
        }

        prompt = get_prompt_for_market(market_data)

        # Should show price as percentage
        assert "73" in prompt

    def test_prompt_includes_volume(self):
        """All prompts should include volume"""
        market_data = {
            "question": "Test market",
            "category": "other",
            "yes_price": 0.5,
            "volume": 123456,
            "closes_at": "2025-01-01",
        }

        prompt = get_prompt_for_market(market_data)

        # Should include volume (likely formatted with commas)
        assert "123" in prompt

    def test_prompt_includes_closes_at(self):
        """All prompts should include closes_at timestamp"""
        market_data = {
            "question": "Test market",
            "category": "other",
            "yes_price": 0.5,
            "volume": 1000,
            "closes_at": "2025-06-15T00:00:00Z",
        }

        prompt = get_prompt_for_market(market_data)

        assert "2025-06-15" in prompt

    def test_get_prompt_metadata(self):
        """Metadata should include version and categories"""
        metadata = get_prompt_metadata()

        assert "version" in metadata
        assert "categories" in metadata
        assert metadata["version"] == PROMPT_VERSION

        # Should list all categories
        categories = metadata["categories"]
        assert "politics" in categories
        assert "crypto" in categories
        assert "sports" in categories
        assert "macro" in categories

    def test_prompt_token_estimates(self):
        """Metadata should include token estimates"""
        metadata = get_prompt_metadata()

        assert "base_prompt_tokens_estimate" in metadata
        assert "category_prompt_tokens_estimate" in metadata

        assert isinstance(metadata["base_prompt_tokens_estimate"], int)
        assert isinstance(metadata["category_prompt_tokens_estimate"], int)

        # Estimates should be reasonable
        assert 50 <= metadata["base_prompt_tokens_estimate"] <= 500
        assert 100 <= metadata["category_prompt_tokens_estimate"] <= 1000

    def test_all_category_prompts_valid_json_schema(self):
        """All category prompts should request valid JSON output"""
        categories_to_test = [
            ("politics", get_politics_prompt),
            ("crypto", get_crypto_prompt),
            ("sports", get_sports_prompt),
            ("macro", get_macro_prompt),
            ("other", get_generic_prompt),
        ]

        market_data = {
            "question": "Test?",
            "yes_price": 0.5,
            "volume": 1000,
            "closes_at": "2025-01-01",
        }

        for category, prompt_fn in categories_to_test:
            prompt = prompt_fn(market_data)

            # Should include JSON instruction
            assert "JSON" in prompt or "json" in prompt

            # Should specify schema fields
            assert "fair_probability" in prompt
            assert "confidence" in prompt
            assert "edge_bps" in prompt
            assert "reasoning" in prompt
            assert "action" in prompt
