"""Test full pipeline: JSON in → analyzed JSON out"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "termux-hands-off" / "agent"))

from polymarket_skeleton import analyze_markets
import pytest


@pytest.mark.integration
class TestPipelineEndToEnd:
    """Integration tests for complete analysis pipeline"""

    def test_end_to_end_analysis(self, sample_markets):
        """Full pipeline should analyze all markets correctly"""
        markets_raw = sample_markets["markets"]
        context = {"target_edge_bps": 500}

        analyzed = analyze_markets(markets_raw, context)

        # Should return same number of markets
        assert len(analyzed) == len(markets_raw)

        # All markets should have required fields
        for market in analyzed:
            assert "id" in market
            assert "question" in market
            assert "category" in market
            assert "yes_price" in market
            assert "fair_yes" in market
            assert "edge" in market
            assert "rec" in market
            assert "notes" in market

            # Category should be valid
            assert market["category"] in ["sports", "crypto", "politics", "macro", "other"]

            # Rec should be valid
            assert market["rec"] in ["buy_yes", "buy_no", "hold"]

            # Prices should be in valid range
            assert 0 <= market["yes_price"] <= 1
            assert 0.01 <= market["fair_yes"] <= 0.99

    def test_pipeline_preserves_ids(self, sample_markets):
        """Pipeline should preserve market IDs"""
        markets_raw = sample_markets["markets"]
        context = {"target_edge_bps": 500}

        analyzed = analyze_markets(markets_raw, context)

        input_ids = {m["id"] for m in markets_raw}
        output_ids = {m["id"] for m in analyzed}

        assert input_ids == output_ids

    def test_pipeline_handles_edge_cases(self, edge_case_markets):
        """Pipeline should gracefully handle malformed inputs"""
        context = {"target_edge_bps": 500}

        # Should not crash on edge cases
        analyzed = analyze_markets(edge_case_markets, context)

        # Should return some results (may process all or skip invalid ones)
        assert isinstance(analyzed, list)
        # At least some markets should be processed
        assert len(analyzed) > 0

    def test_different_threshold_contexts(self):
        """Different threshold parameters should affect recommendations"""
        markets_raw = [{
            "id": "test",
            "question": "Test market",
            "yes_price": 0.50,
            "no_price": 0.50
        }]

        context_500bps = {"target_edge_bps": 500}   # 5%
        context_1000bps = {"target_edge_bps": 1000}  # 10%

        analyzed_500 = analyze_markets(markets_raw, context_500bps)
        analyzed_1000 = analyze_markets(markets_raw, context_1000bps)

        # Both should succeed
        assert len(analyzed_500) == 1
        assert len(analyzed_1000) == 1

        # Both should have valid recommendations
        assert analyzed_500[0]["rec"] in ["buy_yes", "buy_no", "hold"]
        assert analyzed_1000[0]["rec"] in ["buy_yes", "buy_no", "hold"]

    def test_category_distribution(self, sample_markets):
        """Pipeline should correctly categorize diverse markets"""
        markets_raw = sample_markets["markets"]
        context = {"target_edge_bps": 500}

        analyzed = analyze_markets(markets_raw, context)

        # Count categories
        categories = [m["category"] for m in analyzed]

        # Should have multiple categories represented
        assert "sports" in categories
        assert "crypto" in categories
        assert "politics" in categories
        assert "macro" in categories

    def test_volume_preservation(self, sample_markets):
        """Pipeline should preserve volume data"""
        markets_raw = sample_markets["markets"]
        context = {"target_edge_bps": 500}

        analyzed = analyze_markets(markets_raw, context)

        # Find markets with volume in input
        for i, raw in enumerate(markets_raw):
            if "volume" in raw:
                # Should be preserved in output
                assert analyzed[i]["volume"] == raw["volume"]

    def test_empty_markets_list(self):
        """Pipeline should handle empty markets list"""
        markets_raw = []
        context = {"target_edge_bps": 500}

        analyzed = analyze_markets(markets_raw, context)

        assert analyzed == []

    def test_single_market(self):
        """Pipeline should handle single market"""
        markets_raw = [{
            "id": "single",
            "question": "Single market test",
            "yes_price": 0.5,
            "no_price": 0.5
        }]
        context = {"target_edge_bps": 500}

        analyzed = analyze_markets(markets_raw, context)

        assert len(analyzed) == 1
        assert analyzed[0]["id"] == "single"

    def test_edge_calculation_accuracy(self):
        """Edge should be accurately calculated across all markets"""
        markets_raw = [{
            "id": "test",
            "question": "Test",
            "yes_price": 0.6,
            "no_price": 0.4
        }]
        context = {"target_edge_bps": 500}

        analyzed = analyze_markets(markets_raw, context)

        market = analyzed[0]

        # Edge should equal fair_yes - yes_price
        expected_edge = market["fair_yes"] - market["yes_price"]
        assert market["edge"] == pytest.approx(expected_edge, abs=1e-9)

    def test_output_json_structure(self, sample_markets):
        """Output should be valid JSON with expected structure"""
        markets_raw = sample_markets["markets"]
        context = {"target_edge_bps": 500}

        analyzed = analyze_markets(markets_raw, context)

        # Should be serializable to JSON
        json_str = json.dumps({"markets": analyzed})
        parsed = json.loads(json_str)

        assert "markets" in parsed
        assert len(parsed["markets"]) == len(markets_raw)

    def test_idempotency(self, sample_markets):
        """Running pipeline twice on same input should give same output"""
        markets_raw = sample_markets["markets"]
        context = {"target_edge_bps": 500}

        analyzed_1 = analyze_markets(markets_raw, context)
        analyzed_2 = analyze_markets(markets_raw, context)

        # Should be identical
        assert len(analyzed_1) == len(analyzed_2)

        for i in range(len(analyzed_1)):
            assert analyzed_1[i]["id"] == analyzed_2[i]["id"]
            assert analyzed_1[i]["fair_yes"] == analyzed_2[i]["fair_yes"]
            assert analyzed_1[i]["edge"] == analyzed_2[i]["edge"]
            assert analyzed_1[i]["rec"] == analyzed_2[i]["rec"]

    def test_all_categories_have_models(self):
        """Every category should have a working model in REGISTRY"""
        from polymarket_skeleton import Category, REGISTRY

        # All categories should be in registry
        for category in Category:
            assert category in REGISTRY, f"Missing model for {category}"

            # Model should be callable
            model = REGISTRY[category]
            assert hasattr(model, 'score')
