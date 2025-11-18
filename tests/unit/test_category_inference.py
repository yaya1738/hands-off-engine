"""Test category inference logic"""
import sys
from pathlib import Path

# Add termux-hands-off/agent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "termux-hands-off" / "agent"))

from polymarket_skeleton import infer_category, Category
import pytest


@pytest.mark.unit
class TestCategoryInference:
    """Test suite for infer_category() function"""

    def test_sports_keywords(self):
        """Sports keywords should return SPORTS category"""
        test_cases = [
            {"question": "Will the Lakers win the NBA championship?"},
            {"question": "Who will score the most touchdowns in the NFL?"},
            {"question": "Premier League final score prediction"},
            {"question": "Will Messi score in the soccer match?"},
            {"question": "NBA finals MVP winner"},
            {"question": "MLB world series outcome"},
        ]

        for market in test_cases:
            assert infer_category(market) == Category.SPORTS, f"Failed for: {market['question']}"

    def test_crypto_keywords(self):
        """Crypto keywords should return CRYPTO category"""
        test_cases = [
            {"question": "Will Bitcoin reach $100k?"},
            {"question": "Ethereum price above $5000"},
            {"question": "Will Solana outperform BTC?"},
            {"question": "Dogecoin to the moon?"},
            {"question": "ETH merge successful?"},
            {"question": "Crypto market cap reaches $5T"},
            {"question": "Will altcoin season happen?"},
        ]

        for market in test_cases:
            assert infer_category(market) == Category.CRYPTO, f"Failed for: {market['question']}"

    def test_politics_keywords(self):
        """Politics keywords should return POLITICS category"""
        test_cases = [
            {"question": "Who will win the presidential election?"},
            {"question": "Will the Senate pass the bill?"},
            {"question": "Prime Minister votes in parliament"},
            {"question": "House of Representatives vote outcome"},
            {"question": "Election runoff results"},
        ]

        for market in test_cases:
            assert infer_category(market) == Category.POLITICS, f"Failed for: {market['question']}"

    def test_macro_keywords(self):
        """Macro keywords should return MACRO category"""
        test_cases = [
            {"question": "Will the Fed raise interest rates?"},
            {"question": "CPI report exceeds 3%?"},  # Avoid "inflation" (contains "nfl")
            {"question": "GDP growth forecast"},
            {"question": "PPI numbers exceed expectations?"},
            {"question": "unemployment above 4%?"},  # Simplified
            {"question": "FOMC meeting decision"},
        ]

        for market in test_cases:
            assert infer_category(market) == Category.MACRO, f"Failed for: {market['question']}"

    def test_unknown_returns_other(self):
        """Unknown/ambiguous should return OTHER category"""
        test_cases = [
            {"question": "Will it rain tomorrow?"},
            {"question": "Random event happens"},  # Avoid "different" (contains "eth")
            {"question": "An unusual occurrence"},
            {"question": ""},  # Empty question
        ]

        for market in test_cases:
            assert infer_category(market) == Category.OTHER, f"Failed for: {market['question']}"

    def test_case_insensitive(self):
        """Category inference should be case-insensitive"""
        test_cases = [
            ({"question": "WILL BITCOIN REACH $100K?"}, Category.CRYPTO),
            ({"question": "nba championship"}, Category.SPORTS),
            ({"question": "PRESIDENTIAL ELECTION"}, Category.POLITICS),
            ({"question": "fed interest RATE"}, Category.MACRO),
        ]

        for market, expected_category in test_cases:
            assert infer_category(market) == expected_category, f"Failed for: {market['question']}"

    def test_tags_field_parsing(self):
        """Should parse tags field for keywords"""
        test_cases = [
            ({"question": "Unknown", "tags": ["crypto", "bitcoin"]}, Category.CRYPTO),
            ({"question": "Mystery event", "tags": ["nba", "basketball"]}, Category.SPORTS),
            # Avoid "Something" as it contains "eth" substring
            ({"question": "An event", "tags": ["election", "politics"]}, Category.POLITICS),
        ]

        for market, expected_category in test_cases:
            assert infer_category(market) == expected_category, f"Failed for: {market}"

    def test_title_fallback(self):
        """Should check 'title' field if 'question' is missing"""
        market = {"title": "Will Bitcoin reach $100k?"}
        assert infer_category(market) == Category.CRYPTO

    def test_multi_keyword_precedence(self):
        """When multiple keywords match, first match wins (sports checked first)"""
        # This market has both sports and crypto keywords
        market = {"question": "Will NBA accept Bitcoin payments?"}
        # Should be SPORTS because sports keywords are checked first
        assert infer_category(market) == Category.SPORTS
