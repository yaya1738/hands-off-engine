"""Integration tests for decider with LLM alpha report"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from decider.ho_decider import build_decision_report, write_decision_report
import pytest


@pytest.mark.integration
class TestDeciderIntegration:
    """Integration tests for complete decider flow"""

    def test_decider_without_llm_report(self, tmp_path):
        """Should generate decision report even without LLM data"""
        # Use tmp_path for testing
        llm_path = tmp_path / "llm_alpha_report.json"
        decision_path = tmp_path / "decision_report.json"

        # Don't create LLM report - test missing file

        # Build and write report
        report = build_decision_report(llm_report_path=llm_path)
        write_decision_report(report, decision_path)

        # Verify file was created
        assert decision_path.exists()

        # Load and verify structure
        with open(decision_path) as f:
            saved_report = json.load(f)

        assert saved_report["dry_run"] is True
        assert saved_report["llm_alpha"]["enabled"] is False
        assert "reason" in saved_report["llm_alpha"]

    def test_decider_with_valid_llm_report(self, tmp_path):
        """Should integrate LLM data when available"""
        # Create LLM alpha report
        llm_path = tmp_path / "llm_alpha_report.json"
        llm_data = {
            "generated_at": "2025-11-18T08:00:00+00:00",
            "total_markets": 5,
            "llm_analyzed": 5,
            "fallback_count": 0,
            "analyst_status": {
                "dry_run": True,
                "has_llm_backend": True,
            },
            "markets": [
                {
                    "id": "market-1",
                    "slug": "btc-100k-eoy",
                    "ticker": "BTC100K",
                    "question": "Bitcoin reaches $100k by EOY?",
                    "category": "crypto",
                    "yes_price": 0.55,
                    "volume": 1000000,
                    "analysis_source": "llm",
                    "llm_analysis": {
                        "fair_probability": 65.0,
                        "edge_bps": 1000,
                        "action": "buy_yes",
                        "confidence": "high",
                        "reasoning": "Strong fundamentals and momentum",
                    },
                },
                {
                    "id": "market-2",
                    "question": "Ethereum reaches $5k?",
                    "category": "crypto",
                    "yes_price": 0.4,
                    "analysis_source": "llm",
                    "llm_analysis": {
                        "fair_probability": 50.0,
                        "edge_bps": 500,
                        "action": "buy_yes",
                        "confidence": "medium",
                        "reasoning": "Moderate upside",
                    },
                },
                {
                    "id": "market-3",
                    "question": "Lakers win championship?",
                    "category": "sports",
                    "yes_price": 0.3,
                    "analysis_source": "llm",
                    "llm_analysis": {
                        "fair_probability": 25.0,
                        "edge_bps": -500,
                        "action": "buy_no",
                        "confidence": "low",
                        "reasoning": "Overpriced",
                    },
                },
            ],
        }
        llm_path.write_text(json.dumps(llm_data))

        decision_path = tmp_path / "decision_report.json"

        # Build and write report
        report = build_decision_report(llm_report_path=llm_path)
        write_decision_report(report, decision_path)

        # Verify file was created
        assert decision_path.exists()

        # Load and verify
        with open(decision_path) as f:
            saved_report = json.load(f)

        # Check LLM alpha section
        llm_alpha = saved_report["llm_alpha"]
        assert llm_alpha["enabled"] is True
        assert llm_alpha["total_markets"] == 5
        assert llm_alpha["llm_analyzed"] == 5
        assert llm_alpha["fallback_count"] == 0
        assert llm_alpha["dry_run"] is True

        # Check top candidates are included
        assert len(llm_alpha["top_candidates"]) == 3

        # First candidate should be market-1 (highest absolute edge)
        top_candidate = llm_alpha["top_candidates"][0]
        assert top_candidate["market_id"] == "market-1"
        assert top_candidate["question"] == "Bitcoin reaches $100k by EOY?"
        assert top_candidate["fair_probability"] == 65.0
        assert top_candidate["edge_bps"] == 1000
        assert top_candidate["edge_pct_points"] == 10.0
        assert top_candidate["recommendation"] == "buy_yes"
        assert top_candidate["confidence"] == "high"

    def test_decider_with_malformed_llm_report(self, tmp_path):
        """Should handle malformed LLM report gracefully"""
        # Create malformed LLM report
        llm_path = tmp_path / "llm_alpha_report.json"
        llm_path.write_text("{ invalid json }")

        decision_path = tmp_path / "decision_report.json"

        # Should not crash
        report = build_decision_report(llm_report_path=llm_path)
        write_decision_report(report, decision_path)

        # Verify report was still created
        assert decision_path.exists()

        with open(decision_path) as f:
            saved_report = json.load(f)

        # LLM alpha should be disabled
        assert saved_report["llm_alpha"]["enabled"] is False

    def test_decision_report_json_structure(self, tmp_path):
        """Should produce well-formed JSON with all expected sections"""
        # Setup paths
        llm_path = tmp_path / "llm_alpha_report.json"
        decision_path = tmp_path / "decision_report.json"

        # Create minimal LLM report
        llm_data = {
            "generated_at": "2025-11-18T08:00:00+00:00",
            "total_markets": 1,
            "llm_analyzed": 1,
            "fallback_count": 0,
            "analyst_status": {"dry_run": True},
            "markets": [],
        }
        llm_path.write_text(json.dumps(llm_data))

        # Generate report
        report = build_decision_report(llm_report_path=llm_path)
        write_decision_report(report, decision_path)

        # Verify JSON is valid and well-formed
        with open(decision_path) as f:
            saved_report = json.load(f)

        # Check all required top-level keys
        required_keys = [
            "generated_at",
            "version",
            "dry_run",
            "llm_alpha",
            "risk_metrics",
            "infrastructure",
            "polymarket",
        ]
        for key in required_keys:
            assert key in saved_report, f"Missing required key: {key}"

        # Verify types
        assert isinstance(saved_report["generated_at"], str)
        assert isinstance(saved_report["version"], str)
        assert isinstance(saved_report["dry_run"], bool)
        assert isinstance(saved_report["llm_alpha"], dict)
        assert isinstance(saved_report["polymarket"]["orders"], list)
