"""Integration tests for LLM Polymarket pipeline"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm.ho_llm_polymarket import load_markets, analyze_markets_with_llm, write_output
from llm.market_analyst import LLMMarketAnalyst
from llm.backend_selector import Priority
import pytest


@pytest.mark.integration
class TestLLMPipeline:
    """Integration tests for complete LLM analysis pipeline"""

    def test_load_markets_from_dict_format(self, tmp_path):
        """Should load markets from {"markets": [...]} format"""
        input_file = tmp_path / "compact.json"

        data = {
            "markets": [
                {
                    "id": "market-1",
                    "question": "Will Bitcoin reach $100k?",
                    "category": "crypto",
                    "yes_price": 0.62,
                    "volume": 500000,
                },
                {
                    "id": "market-2",
                    "question": "Will the Senate pass the bill?",
                    "category": "politics",
                    "yes_price": 0.55,
                    "volume": 100000,
                },
            ]
        }

        input_file.write_text(json.dumps(data))

        markets = load_markets(input_file)

        assert len(markets) == 2
        assert markets[0]["id"] == "market-1"
        assert markets[1]["id"] == "market-2"

    def test_load_markets_from_list_format(self, tmp_path):
        """Should load markets from [...] format"""
        input_file = tmp_path / "compact.json"

        data = [
            {"id": "m1", "question": "Q1", "yes_price": 0.5},
            {"id": "m2", "question": "Q2", "yes_price": 0.6},
        ]

        input_file.write_text(json.dumps(data))

        markets = load_markets(input_file)

        assert len(markets) == 2

    def test_load_markets_missing_file(self, tmp_path):
        """Should return empty list if file doesn't exist"""
        input_file = tmp_path / "nonexistent.json"

        markets = load_markets(input_file)

        assert markets == []

    def test_load_markets_invalid_json(self, tmp_path):
        """Should return empty list if JSON is invalid"""
        input_file = tmp_path / "invalid.json"
        input_file.write_text("not valid json")

        markets = load_markets(input_file)

        assert markets == []

    def test_analyze_markets_with_llm_dryrun(self):
        """Should analyze markets in DRYRUN mode"""
        analyst = LLMMarketAnalyst(dry_run=True)

        markets = [
            {
                "id": "test-1",
                "question": "Will Bitcoin reach $100k?",
                "category": "crypto",
                "yes_price": 0.62,
                "volume": 500000,
                "closes_at": "2025-12-31",
            }
        ]

        results = analyze_markets_with_llm(markets, analyst)

        assert len(results) == 1

        result = results[0]
        assert result["id"] == "test-1"
        assert result["question"] == "Will Bitcoin reach $100k?"
        assert result["category"] == "crypto"

        # Should have analysis (either LLM or fallback)
        assert "analysis_source" in result
        assert result["analysis_source"] in ["llm", "fallback_naive"]

    def test_analyze_markets_with_max_limit(self):
        """Should respect max_markets limit"""
        analyst = LLMMarketAnalyst(dry_run=True)

        markets = [
            {"id": f"market-{i}", "question": f"Q{i}", "category": "other", "yes_price": 0.5}
            for i in range(10)
        ]

        results = analyze_markets_with_llm(markets, analyst, max_markets=3)

        # Should only analyze first 3
        assert len(results) == 3

    def test_analyze_markets_includes_all_fields(self):
        """Analysis results should include all required fields"""
        analyst = LLMMarketAnalyst(dry_run=True)

        markets = [
            {
                "id": "test-1",
                "question": "Test market?",
                "category": "sports",
                "yes_price": 0.55,
                "volume": 75000,
                "closes_at": "2025-06-15",
            }
        ]

        results = analyze_markets_with_llm(markets, analyst)

        result = results[0]

        # Should preserve original market fields
        assert result["id"] == "test-1"
        assert result["question"] == "Test market?"
        assert result["category"] == "sports"
        assert result["yes_price"] == 0.55
        assert result["volume"] == 75000
        assert result["closes_at"] == "2025-06-15"

        # Should add analysis fields
        assert "llm_analysis" in result
        assert "analysis_source" in result

    def test_write_output_creates_valid_json(self, tmp_path):
        """Should write valid JSON output"""
        output_file = tmp_path / "llm_alpha_report.json"

        results = [
            {
                "id": "test-1",
                "question": "Test?",
                "category": "other",
                "yes_price": 0.5,
                "volume": 1000,
                "closes_at": "2025-01-01",
                "llm_analysis": None,
                "analysis_source": "fallback_naive",
            }
        ]

        analyst_status = {
            "dry_run": True,
            "has_llm_backend": False,
            "available_backends": [],
            "fallback_enabled": True,
        }

        write_output(results, output_file, analyst_status)

        # Should create file
        assert output_file.exists()

        # Should be valid JSON
        data = json.loads(output_file.read_text())

        assert "generated_at" in data
        assert "analyst_status" in data
        assert "total_markets" in data
        assert "llm_analyzed" in data
        assert "fallback_count" in data
        assert "markets" in data

        assert data["total_markets"] == 1
        assert data["llm_analyzed"] == 0
        assert data["fallback_count"] == 1

    def test_write_output_counts_llm_vs_fallback(self, tmp_path):
        """Should correctly count LLM vs fallback analyses"""
        output_file = tmp_path / "output.json"

        results = [
            {"id": "1", "question": "Q1", "analysis_source": "llm"},
            {"id": "2", "question": "Q2", "analysis_source": "llm"},
            {"id": "3", "question": "Q3", "analysis_source": "fallback_naive"},
        ]

        analyst_status = {"dry_run": True}

        write_output(results, output_file, analyst_status)

        data = json.loads(output_file.read_text())

        assert data["total_markets"] == 3
        assert data["llm_analyzed"] == 2
        assert data["fallback_count"] == 1

    def test_end_to_end_pipeline(self, tmp_path):
        """Full end-to-end test: load → analyze → write"""
        # Setup input
        input_file = tmp_path / "polymarket-compact.json"
        output_file = tmp_path / "llm_alpha_report.json"

        input_data = {
            "markets": [
                {
                    "id": "crypto-1",
                    "question": "Will Bitcoin reach $100k in 2025?",
                    "category": "crypto",
                    "yes_price": 0.62,
                    "volume": 500000,
                    "closes_at": "2025-12-31",
                },
                {
                    "id": "politics-1",
                    "question": "Will the Senate pass the bill?",
                    "category": "politics",
                    "yes_price": 0.55,
                    "volume": 100000,
                    "closes_at": "2025-03-01",
                },
            ]
        }

        input_file.write_text(json.dumps(input_data))

        # Load markets
        markets = load_markets(input_file)
        assert len(markets) == 2

        # Analyze with LLM (DRYRUN)
        analyst = LLMMarketAnalyst(dry_run=True, default_priority=Priority.QUALITY)
        results = analyze_markets_with_llm(markets, analyst)

        assert len(results) == 2

        # Write output
        status = analyst.get_status()
        write_output(results, output_file, status)

        # Verify output
        assert output_file.exists()
        output_data = json.loads(output_file.read_text())

        assert output_data["total_markets"] == 2
        assert len(output_data["markets"]) == 2

        # All fields should be preserved
        assert output_data["markets"][0]["id"] == "crypto-1"
        assert output_data["markets"][0]["category"] == "crypto"
        assert output_data["markets"][1]["id"] == "politics-1"
        assert output_data["markets"][1]["category"] == "politics"

    def test_pipeline_handles_malformed_market_data(self):
        """Pipeline should handle markets with missing fields gracefully"""
        analyst = LLMMarketAnalyst(dry_run=True)

        # Market with missing optional fields
        markets = [
            {
                "id": "minimal",
                "question": "Minimal market?",
                # Missing: category, volume, closes_at
                "yes_price": 0.5,
            }
        ]

        # Should not crash
        results = analyze_markets_with_llm(markets, analyst)

        assert len(results) == 1
        assert results[0]["id"] == "minimal"

    def test_pipeline_preserves_market_order(self):
        """Pipeline should preserve order of markets"""
        analyst = LLMMarketAnalyst(dry_run=True)

        markets = [
            {"id": "first", "question": "Q1", "yes_price": 0.5},
            {"id": "second", "question": "Q2", "yes_price": 0.6},
            {"id": "third", "question": "Q3", "yes_price": 0.7},
        ]

        results = analyze_markets_with_llm(markets, analyst)

        assert results[0]["id"] == "first"
        assert results[1]["id"] == "second"
        assert results[2]["id"] == "third"

    def test_output_json_is_serializable(self, tmp_path):
        """Output should be valid JSON (no datetime objects, etc.)"""
        output_file = tmp_path / "output.json"

        results = [
            {"id": "test", "question": "Test?", "analysis_source": "fallback_naive"}
        ]

        status = {"dry_run": True}

        write_output(results, output_file, status)

        # Should be able to parse
        data = json.loads(output_file.read_text())

        # Should be able to serialize again (no non-JSON objects)
        json.dumps(data)  # Should not raise
