"""Unit tests for LLM Market Analyst"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm.market_analyst import LLMMarketAnalyst, LLMOpinion
from llm.backend_selector import Backend, Priority
import pytest


@pytest.mark.unit
class TestLLMOpinion:
    """Test suite for LLMOpinion dataclass"""

    def test_llm_opinion_creation(self):
        """Should create LLMOpinion with all required fields"""
        opinion = LLMOpinion(
            fair_probability=62.5,
            confidence="medium",
            edge_bps=250,
            reasoning="Market underpriced",
            action="buy_yes",
            backend_used="claude-api",
            model_name="claude-sonnet-4",
            prompt_version="v1.0.0",
            tokens_used=350,
        )

        assert opinion.fair_probability == 62.5
        assert opinion.confidence == "medium"
        assert opinion.edge_bps == 250
        assert opinion.reasoning == "Market underpriced"
        assert opinion.action == "buy_yes"
        assert opinion.backend_used == "claude-api"
        assert opinion.tokens_used == 350

    def test_llm_opinion_to_dict(self):
        """Should convert to dict for serialization"""
        opinion = LLMOpinion(
            fair_probability=55.0,
            confidence="high",
            edge_bps=-200,
            reasoning="Test reasoning",
            action="buy_no",
            backend_used="openrouter-gpt4",
            model_name="gpt-4-turbo",
            prompt_version="v1.0.0",
        )

        data = opinion.to_dict()

        assert isinstance(data, dict)
        assert data["fair_probability"] == 55.0
        assert data["confidence"] == "high"
        assert data["edge_bps"] == -200
        assert data["reasoning"] == "Test reasoning"
        assert data["action"] == "buy_no"

    def test_llm_opinion_to_opinion_format(self):
        """Should convert to polymarket_skeleton Opinion format"""
        opinion = LLMOpinion(
            fair_probability=75.0,  # 75%
            confidence="high",
            edge_bps=500,  # 5%
            reasoning="Strong fundamentals",
            action="buy_yes",
            backend_used="claude-api",
            model_name="claude-sonnet-4",
            prompt_version="v1.0.0",
        )

        skeleton_format = opinion.to_opinion_format()

        # Should convert percentage to decimal
        assert skeleton_format["fair_yes"] == 0.75

        # Should convert bps to decimal
        assert skeleton_format["edge"] == 0.05

        # Should convert action format
        assert skeleton_format["rec"] == "buy yes"

        # Should include notes with backend and reasoning
        assert "claude-api" in skeleton_format["notes"]
        assert "Strong fundamentals" in skeleton_format["notes"]
        assert "high confidence" in skeleton_format["notes"]


@pytest.mark.unit
class TestLLMMarketAnalyst:
    """Test suite for LLMMarketAnalyst"""

    def test_analyst_initialization_default(self):
        """Should initialize with default DRYRUN settings"""
        analyst = LLMMarketAnalyst()

        assert analyst.dry_run is True
        assert analyst.enable_fallback is True

    def test_analyst_initialization_custom(self):
        """Should allow custom initialization"""
        analyst = LLMMarketAnalyst(
            default_priority=Priority.SPEED,
            enable_fallback=False,
            dry_run=False,
        )

        assert analyst.backend_selector.default_priority == Priority.SPEED
        assert analyst.enable_fallback is False
        assert analyst.dry_run is False

    def test_analyst_get_status(self, monkeypatch):
        """Should return status information"""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        analyst = LLMMarketAnalyst()
        status = analyst.get_status()

        assert "dry_run" in status
        assert "has_llm_backend" in status
        assert "available_backends" in status
        assert "fallback_enabled" in status

        assert status["dry_run"] is True
        assert isinstance(status["available_backends"], list)

    def test_analyze_market_dryrun_mode(self):
        """Should simulate LLM call in DRYRUN mode"""
        analyst = LLMMarketAnalyst(dry_run=True)

        market_data = {
            "question": "Will Bitcoin reach $100k?",
            "category": "crypto",
            "yes_price": 0.62,
            "volume": 500000,
            "closes_at": "2025-12-31",
        }

        opinion = analyst.analyze_market(market_data)

        # In DRYRUN mode, should return simulated opinion
        # (unless no backends available, then returns None)
        if opinion:
            assert isinstance(opinion, LLMOpinion)
            assert 0 <= opinion.fair_probability <= 100
            assert opinion.confidence in ["low", "medium", "high"]
            assert opinion.action in ["buy_yes", "buy_no", "avoid"]
            assert "DRYRUN" in opinion.reasoning or "Simulated" in opinion.reasoning

    def test_analyze_market_no_backends_returns_none(self, monkeypatch):
        """Should return None when no LLM backends available"""
        # Clear all API keys
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        analyst = LLMMarketAnalyst()

        market_data = {
            "question": "Test market",
            "category": "other",
            "yes_price": 0.5,
            "volume": 1000,
            "closes_at": "2025-01-01",
        }

        opinion = analyst.analyze_market(market_data)

        # With no backends, should return None (caller falls back to naive)
        assert opinion is None

    def test_parse_llm_response_valid_json(self):
        """Should parse valid JSON response"""
        analyst = LLMMarketAnalyst()

        response = json.dumps({
            "fair_probability": 65.5,
            "confidence": "medium",
            "edge_bps": 350,
            "reasoning": "Market slightly undervalued",
            "action": "buy_yes",
        })

        market_data = {"yes_price": 0.62}

        opinion = analyst._parse_llm_response(response, Backend.CLAUDE_API, market_data)

        assert opinion is not None
        assert opinion.fair_probability == 65.5
        assert opinion.confidence == "medium"
        assert opinion.edge_bps == 350
        assert opinion.action == "buy_yes"

    def test_parse_llm_response_invalid_json(self):
        """Should return None for invalid JSON"""
        analyst = LLMMarketAnalyst()

        response = "This is not valid JSON"

        opinion = analyst._parse_llm_response(response, Backend.CLAUDE_API, {})

        assert opinion is None

    def test_parse_llm_response_missing_fields(self):
        """Should return None if required fields missing"""
        analyst = LLMMarketAnalyst()

        # Missing 'reasoning' field
        response = json.dumps({
            "fair_probability": 50.0,
            "confidence": "low",
            "edge_bps": 0,
            "action": "avoid",
        })

        opinion = analyst._parse_llm_response(response, Backend.CLAUDE_API, {})

        assert opinion is None

    def test_parse_llm_response_invalid_probability(self):
        """Should reject invalid fair_probability values"""
        analyst = LLMMarketAnalyst()

        # Probability > 100
        response = json.dumps({
            "fair_probability": 150.0,
            "confidence": "high",
            "edge_bps": 500,
            "reasoning": "Invalid",
            "action": "buy_yes",
        })

        opinion = analyst._parse_llm_response(response, Backend.CLAUDE_API, {})

        assert opinion is None

    def test_parse_llm_response_invalid_confidence(self):
        """Should reject invalid confidence values"""
        analyst = LLMMarketAnalyst()

        response = json.dumps({
            "fair_probability": 50.0,
            "confidence": "invalid",  # Not low/medium/high
            "edge_bps": 0,
            "reasoning": "Test",
            "action": "avoid",
        })

        opinion = analyst._parse_llm_response(response, Backend.CLAUDE_API, {})

        assert opinion is None

    def test_parse_llm_response_invalid_action(self):
        """Should reject invalid action values"""
        analyst = LLMMarketAnalyst()

        response = json.dumps({
            "fair_probability": 50.0,
            "confidence": "medium",
            "edge_bps": 0,
            "reasoning": "Test",
            "action": "invalid_action",  # Not buy_yes/buy_no/avoid
        })

        opinion = analyst._parse_llm_response(response, Backend.CLAUDE_API, {})

        assert opinion is None

    def test_simulate_llm_call_returns_valid_json(self):
        """DRYRUN simulation should return valid JSON"""
        analyst = LLMMarketAnalyst()

        market_data = {
            "question": "Test market",
            "yes_price": 0.5,
            "volume": 1000,
            "closes_at": "2025-01-01",
        }

        response = analyst._simulate_llm_call(market_data, Backend.CLAUDE_API, "test prompt")

        # Should be valid JSON
        data = json.loads(response)

        assert "fair_probability" in data
        assert "confidence" in data
        assert "edge_bps" in data
        assert "reasoning" in data
        assert "action" in data

    def test_simulate_llm_call_realistic_values(self):
        """DRYRUN simulation should produce realistic values"""
        analyst = LLMMarketAnalyst()

        market_data = {
            "question": "Test market",
            "yes_price": 0.60,
            "volume": 1000,
            "closes_at": "2025-01-01",
        }

        response = analyst._simulate_llm_call(market_data, Backend.CLAUDE_API, "test prompt")
        data = json.loads(response)

        # Probabilities should be in valid range
        assert 5 <= data["fair_probability"] <= 95

        # Should have valid confidence
        assert data["confidence"] in ["low", "medium", "high"]

        # Should have valid action
        assert data["action"] in ["buy_yes", "buy_no", "avoid"]

    def test_analyze_market_with_priority_override(self):
        """Should allow priority override per request"""
        analyst = LLMMarketAnalyst(default_priority=Priority.QUALITY)

        market_data = {
            "question": "Test",
            "category": "other",
            "yes_price": 0.5,
            "volume": 1000,
            "closes_at": "2025-01-01",
        }

        # Should not crash with different priority
        opinion = analyst.analyze_market(market_data, priority=Priority.SPEED)

        # Behavior depends on available backends, but should not crash
        assert opinion is None or isinstance(opinion, LLMOpinion)

    def test_opinion_format_converts_buy_yes_correctly(self):
        """buy_yes action should convert to 'buy yes' in skeleton format"""
        opinion = LLMOpinion(
            fair_probability=70.0,
            confidence="high",
            edge_bps=700,
            reasoning="Test",
            action="buy_yes",
            backend_used="test",
            model_name="test",
            prompt_version="v1.0.0",
        )

        fmt = opinion.to_opinion_format()

        assert fmt["rec"] == "buy yes"  # Underscore should become space

    def test_opinion_format_converts_buy_no_correctly(self):
        """buy_no action should convert to 'buy no' in skeleton format"""
        opinion = LLMOpinion(
            fair_probability=30.0,
            confidence="medium",
            edge_bps=-700,
            reasoning="Test",
            action="buy_no",
            backend_used="test",
            model_name="test",
            prompt_version="v1.0.0",
        )

        fmt = opinion.to_opinion_format()

        assert fmt["rec"] == "buy no"
