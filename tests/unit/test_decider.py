"""Unit tests for decider module"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from decider.ho_decider import (
    load_llm_alpha_report,
    extract_top_llm_candidates,
    build_llm_alpha_section,
    build_decision_report,
)
import pytest


@pytest.mark.unit
class TestDecider:
    """Tests for decider functionality"""

    def test_load_llm_alpha_report_missing_file(self, tmp_path):
        """Should return None and not crash when file is missing"""
        nonexistent = tmp_path / "nonexistent.json"

        result = load_llm_alpha_report(nonexistent)

        assert result is None

    def test_load_llm_alpha_report_invalid_json(self, tmp_path):
        """Should return None when JSON is malformed"""
        invalid_file = tmp_path / "invalid.json"
        invalid_file.write_text("not valid json{")

        result = load_llm_alpha_report(invalid_file)

        assert result is None

    def test_load_llm_alpha_report_missing_required_fields(self, tmp_path):
        """Should return None when required fields are missing"""
        incomplete_file = tmp_path / "incomplete.json"
        incomplete_file.write_text(json.dumps({"total_markets": 5}))

        result = load_llm_alpha_report(incomplete_file)

        assert result is None

    def test_load_llm_alpha_report_valid(self, tmp_path):
        """Should load valid LLM alpha report successfully"""
        valid_file = tmp_path / "valid.json"
        data = {
            "total_markets": 5,
            "llm_analyzed": 5,
            "fallback_count": 0,
            "markets": [
                {
                    "id": "btc-100k",
                    "question": "Bitcoin reaches $100k?",
                    "category": "crypto",
                    "yes_price": 0.5,
                    "analysis_source": "llm",
                    "llm_analysis": {
                        "fair_probability": 48.5,
                        "edge_bps": -150,
                        "action": "buy_no",
                        "confidence": "medium",
                    },
                }
            ],
        }
        valid_file.write_text(json.dumps(data))

        result = load_llm_alpha_report(valid_file)

        assert result is not None
        assert result["total_markets"] == 5
        assert result["llm_analyzed"] == 5
        assert len(result["markets"]) == 1

    def test_extract_top_llm_candidates_empty_markets(self):
        """Should handle empty markets list"""
        llm_report = {"markets": []}

        candidates = extract_top_llm_candidates(llm_report, top_n=5)

        assert candidates == []

    def test_extract_top_llm_candidates_sorts_by_abs_edge(self):
        """Should sort candidates by absolute edge (highest first)"""
        llm_report = {
            "markets": [
                {
                    "id": "low-edge",
                    "question": "Low edge market",
                    "category": "other",
                    "yes_price": 0.5,
                    "analysis_source": "llm",
                    "llm_analysis": {
                        "fair_probability": 52.0,
                        "edge_bps": 200,
                        "action": "buy_yes",
                        "confidence": "low",
                    },
                },
                {
                    "id": "high-edge",
                    "question": "High edge market",
                    "category": "crypto",
                    "yes_price": 0.6,
                    "analysis_source": "llm",
                    "llm_analysis": {
                        "fair_probability": 40.0,
                        "edge_bps": -2000,
                        "action": "buy_no",
                        "confidence": "high",
                    },
                },
                {
                    "id": "medium-edge",
                    "question": "Medium edge market",
                    "category": "politics",
                    "yes_price": 0.7,
                    "analysis_source": "llm",
                    "llm_analysis": {
                        "fair_probability": 80.0,
                        "edge_bps": 1000,
                        "action": "buy_yes",
                        "confidence": "medium",
                    },
                },
            ]
        }

        candidates = extract_top_llm_candidates(llm_report, top_n=10)

        # Should be sorted by absolute edge: 2000, 1000, 200
        assert len(candidates) == 3
        assert candidates[0]["market_id"] == "high-edge"
        assert candidates[0]["edge_bps"] == -2000
        assert candidates[1]["market_id"] == "medium-edge"
        assert candidates[1]["edge_bps"] == 1000
        assert candidates[2]["market_id"] == "low-edge"
        assert candidates[2]["edge_bps"] == 200

    def test_extract_top_llm_candidates_respects_top_n(self):
        """Should limit to top_n candidates"""
        llm_report = {
            "markets": [
                {
                    "id": f"market-{i}",
                    "question": f"Q{i}",
                    "category": "test",
                    "yes_price": 0.5,
                    "analysis_source": "llm",
                    "llm_analysis": {
                        "fair_probability": 50.0 + i,
                        "edge_bps": i * 100,
                        "action": "buy_yes",
                        "confidence": "low",
                    },
                }
                for i in range(20)
            ]
        }

        candidates = extract_top_llm_candidates(llm_report, top_n=5)

        assert len(candidates) == 5

    def test_extract_top_llm_candidates_filters_non_llm_markets(self):
        """Should only include markets with LLM analysis"""
        llm_report = {
            "markets": [
                {
                    "id": "llm-market",
                    "question": "LLM analyzed",
                    "category": "crypto",
                    "yes_price": 0.5,
                    "analysis_source": "llm",
                    "llm_analysis": {
                        "fair_probability": 55.0,
                        "edge_bps": 500,
                        "action": "buy_yes",
                        "confidence": "medium",
                    },
                },
                {
                    "id": "fallback-market",
                    "question": "Fallback",
                    "category": "other",
                    "yes_price": 0.5,
                    "analysis_source": "fallback",
                    "llm_analysis": None,
                },
            ]
        }

        candidates = extract_top_llm_candidates(llm_report, top_n=10)

        assert len(candidates) == 1
        assert candidates[0]["market_id"] == "llm-market"

    def test_build_llm_alpha_section_none_report(self):
        """Should return disabled section when report is None"""
        section = build_llm_alpha_section(None)

        assert section["enabled"] is False
        assert "reason" in section

    def test_build_llm_alpha_section_valid_report(self):
        """Should build proper llm_alpha section from valid report"""
        llm_report = {
            "generated_at": "2025-11-18T07:00:00+00:00",
            "total_markets": 3,
            "llm_analyzed": 3,
            "fallback_count": 0,
            "analyst_status": {"dry_run": True},
            "markets": [
                {
                    "id": "market-1",
                    "question": "Question 1",
                    "category": "crypto",
                    "yes_price": 0.5,
                    "analysis_source": "llm",
                    "llm_analysis": {
                        "fair_probability": 60.0,
                        "edge_bps": 1000,
                        "action": "buy_yes",
                        "confidence": "high",
                        "reasoning": "Strong upside",
                    },
                }
            ],
        }

        section = build_llm_alpha_section(llm_report)

        assert section["enabled"] is True
        assert section["generated_at"] == "2025-11-18T07:00:00+00:00"
        assert section["total_markets"] == 3
        assert section["llm_analyzed"] == 3
        assert section["fallback_count"] == 0
        assert section["dry_run"] is True
        assert len(section["top_candidates"]) == 1
        assert section["top_candidates"][0]["market_id"] == "market-1"

    def test_build_decision_report_structure(self):
        """Should build decision report with correct structure"""
        report = build_decision_report()

        # Check top-level structure
        assert "generated_at" in report
        assert "version" in report
        assert "dry_run" in report

        # Check sections exist
        assert "llm_alpha" in report
        assert "risk_metrics" in report
        assert "infrastructure" in report
        assert "polymarket" in report

        # LLM alpha should be disabled if no report exists
        assert "enabled" in report["llm_alpha"]

        # Other sections should be disabled (not implemented yet)
        assert report["risk_metrics"]["enabled"] is False
        assert report["infrastructure"]["enabled"] is False

        # No orders in DRYRUN mode
        assert report["polymarket"]["orders"] == []

    def test_build_decision_report_with_llm_data(self, tmp_path):
        """Should include LLM data when report is available"""
        # Create a valid LLM alpha report
        llm_report_path = tmp_path / "llm_alpha_report.json"
        llm_data = {
            "generated_at": "2025-11-18T07:00:00+00:00",
            "total_markets": 2,
            "llm_analyzed": 2,
            "fallback_count": 0,
            "analyst_status": {"dry_run": True},
            "markets": [
                {
                    "id": "btc",
                    "question": "Bitcoin reaches $100k?",
                    "category": "crypto",
                    "yes_price": 0.5,
                    "analysis_source": "llm",
                    "llm_analysis": {
                        "fair_probability": 55.0,
                        "edge_bps": 500,
                        "action": "buy_yes",
                        "confidence": "medium",
                        "reasoning": "Good odds",
                    },
                }
            ],
        }
        llm_report_path.write_text(json.dumps(llm_data))

        report = build_decision_report(llm_report_path=llm_report_path)

        # LLM alpha should be enabled
        assert report["llm_alpha"]["enabled"] is True
        assert report["llm_alpha"]["total_markets"] == 2
        assert report["llm_alpha"]["llm_analyzed"] == 2
        assert len(report["llm_alpha"]["top_candidates"]) == 1
        assert report["llm_alpha"]["top_candidates"][0]["market_id"] == "btc"
