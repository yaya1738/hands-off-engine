"""Unit tests for LLM Evaluation Framework"""
import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from llm.evaluation import LLMEvaluator, EvaluationReport, Comparison
import pytest


@pytest.mark.unit
class TestLLMEvaluator:
    """Test suite for LLMEvaluator"""

    def test_evaluator_initialization(self):
        """Should initialize with empty comparison state"""
        evaluator = LLMEvaluator()

        assert len(evaluator.comparisons) == 0

    def test_add_comparison_basic(self):
        """Should add a comparison between LLM and naive opinions"""
        evaluator = LLMEvaluator()

        llm_opinion = {
            "fair_probability": 65.0,
            "confidence": "medium",
            "action": "buy_yes",
            "edge_bps": 300,
        }

        naive_opinion = {
            "fair_yes": 0.62,  # 62%
            "edge": 0.0,
            "rec": "avoid",
        }

        evaluator.add_comparison(
            market_id="test-1",
            market_question="Test market?",
            market_category="crypto",
            llm_opinion=llm_opinion,
            naive_opinion=naive_opinion,
        )

        assert len(evaluator.comparisons) == 1

    def test_add_comparison_none_llm_opinion(self):
        """Should handle None LLM opinion gracefully"""
        evaluator = LLMEvaluator()

        naive_opinion = {
            "fair_yes": 0.5,
            "edge": 0.0,
            "rec": "avoid",
        }

        evaluator.add_comparison(
            market_id="test-1",
            market_question="Test?",
            market_category="other",
            llm_opinion=None,
            naive_opinion=naive_opinion,
        )

        assert len(evaluator.comparisons) == 1
        comp = evaluator.comparisons[0]
        assert comp.llm_action is None
        assert comp.llm_fair_probability is None

    def test_directional_agreement_both_buy_yes(self):
        """Should detect agreement when both recommend buy_yes"""
        evaluator = LLMEvaluator()

        llm_opinion = {
            "fair_probability": 70.0,
            "action": "buy_yes",
            "edge_bps": 500,
            "confidence": "high",
        }
        naive_opinion = {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03}

        evaluator.add_comparison("m1", "Q1", "other", llm_opinion, naive_opinion)

        comparison = evaluator.comparisons[0]

        assert comparison.directional_agreement is True

    def test_directional_agreement_both_buy_no(self):
        """Should detect agreement when both recommend buy_no"""
        evaluator = LLMEvaluator()

        llm_opinion = {
            "fair_probability": 30.0,
            "action": "buy_no",
            "edge_bps": -400,
            "confidence": "medium",
        }
        naive_opinion = {"fair_yes": 0.32, "rec": "buy no", "edge": -0.03}

        evaluator.add_comparison("m1", "Q1", "other", llm_opinion, naive_opinion)

        comparison = evaluator.comparisons[0]

        assert comparison.directional_agreement is True

    def test_directional_agreement_both_avoid(self):
        """Should detect agreement when both recommend avoid"""
        evaluator = LLMEvaluator()

        llm_opinion = {
            "fair_probability": 50.0,
            "action": "avoid",
            "edge_bps": 0,
            "confidence": "low",
        }
        naive_opinion = {"fair_yes": 0.51, "rec": "avoid", "edge": 0.0}

        evaluator.add_comparison("m1", "Q1", "other", llm_opinion, naive_opinion)

        comparison = evaluator.comparisons[0]

        assert comparison.directional_agreement is True

    def test_directional_disagreement(self):
        """Should detect disagreement when recommendations differ"""
        evaluator = LLMEvaluator()

        llm_opinion = {
            "fair_probability": 70.0,
            "action": "buy_yes",
            "edge_bps": 600,
            "confidence": "high",
        }
        naive_opinion = {"fair_yes": 0.30, "rec": "buy no", "edge": -0.05}

        evaluator.add_comparison("m1", "Q1", "other", llm_opinion, naive_opinion)

        comparison = evaluator.comparisons[0]

        assert comparison.directional_agreement is False

    def test_probability_delta_calculation(self):
        """Should calculate probability delta correctly"""
        evaluator = LLMEvaluator()

        # LLM: 65%, Naive: 60%
        llm_opinion = {
            "fair_probability": 65.0,
            "action": "buy_yes",
            "edge_bps": 300,
            "confidence": "medium",
        }
        naive_opinion = {"fair_yes": 0.60, "rec": "buy yes", "edge": 0.02}

        evaluator.add_comparison("m1", "Q1", "other", llm_opinion, naive_opinion)

        comparison = evaluator.comparisons[0]

        # Delta should be 5.0 (65 - 60)
        assert abs(comparison.probability_delta - 5.0) < 0.01

    def test_probability_delta_negative(self):
        """Should handle negative delta when LLM < Naive"""
        evaluator = LLMEvaluator()

        # LLM: 55%, Naive: 70%
        llm_opinion = {
            "fair_probability": 55.0,
            "action": "buy_yes",
            "edge_bps": 200,
            "confidence": "low",
        }
        naive_opinion = {"fair_yes": 0.70, "rec": "buy yes", "edge": 0.03}

        evaluator.add_comparison("m1", "Q1", "other", llm_opinion, naive_opinion)

        comparison = evaluator.comparisons[0]

        # Delta should be -15.0 (55 - 70)
        assert abs(comparison.probability_delta - (-15.0)) < 0.01

    def test_edge_delta_calculation(self):
        """Should calculate edge delta correctly"""
        evaluator = LLMEvaluator()

        # LLM: 500 bps, Naive: 300 bps
        llm_opinion = {
            "fair_probability": 70.0,
            "action": "buy_yes",
            "edge_bps": 500,
            "confidence": "high",
        }
        naive_opinion = {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03}  # 300 bps

        evaluator.add_comparison("m1", "Q1", "other", llm_opinion, naive_opinion)

        comparison = evaluator.comparisons[0]

        # Delta should be 200 bps (500 - 300)
        assert abs(comparison.edge_delta_bps - 200) < 1

    def test_comparison_stores_naive_edge_bps(self):
        """Should store naive edge in basis points"""
        evaluator = LLMEvaluator()

        llm_opinion = {
            "fair_probability": 70.0,
            "action": "buy_yes",
            "edge_bps": 500,
            "confidence": "high",
        }
        naive_opinion = {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03}  # 300 bps

        evaluator.add_comparison("m1", "Q1", "other", llm_opinion, naive_opinion)

        comparison = evaluator.comparisons[0]

        assert comparison.naive_edge_bps == 300

    def test_comparison_stores_llm_edge_bps(self):
        """Should store LLM edge in basis points"""
        evaluator = LLMEvaluator()

        llm_opinion = {
            "fair_probability": 70.0,
            "action": "buy_yes",
            "edge_bps": 500,
            "confidence": "high",
        }
        naive_opinion = {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03}

        evaluator.add_comparison("m1", "Q1", "other", llm_opinion, naive_opinion)

        comparison = evaluator.comparisons[0]

        assert comparison.llm_edge_bps == 500

    def test_confidence_edge_alignment_high_aligned(self):
        """Should detect aligned high confidence with large edge"""
        evaluator = LLMEvaluator()

        llm_opinion = {
            "fair_probability": 70.0,
            "action": "buy_yes",
            "edge_bps": 600,  # Large edge
            "confidence": "high",
        }
        naive_opinion = {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03}

        evaluator.add_comparison("m1", "Q1", "other", llm_opinion, naive_opinion)

        comparison = evaluator.comparisons[0]

        assert comparison.confidence_edge_alignment == "aligned"

    def test_confidence_edge_alignment_high_misaligned(self):
        """Should detect misaligned high confidence with small edge"""
        evaluator = LLMEvaluator()

        llm_opinion = {
            "fair_probability": 70.0,
            "action": "buy_yes",
            "edge_bps": 100,  # Small edge
            "confidence": "high",
        }
        naive_opinion = {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03}

        evaluator.add_comparison("m1", "Q1", "other", llm_opinion, naive_opinion)

        comparison = evaluator.comparisons[0]

        assert comparison.confidence_edge_alignment == "misaligned"

    def test_generate_report_empty(self):
        """Should handle empty comparisons"""
        evaluator = LLMEvaluator()

        report = evaluator.generate_report()

        assert report.total_comparisons == 0
        assert report.llm_available_count == 0
        assert report.fallback_count == 0
        assert report.agreement_rate == 0.0
        assert report.avg_probability_delta == 0.0

    def test_generate_report_basic_stats(self):
        """Should calculate basic statistics correctly"""
        evaluator = LLMEvaluator()

        # Add 3 comparisons: 2 agreements, 1 disagreement
        evaluator.add_comparison(
            "m1",
            "Q1",
            "crypto",
            {
                "fair_probability": 70.0,
                "action": "buy_yes",
                "confidence": "high",
                "edge_bps": 500,
            },
            {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03},
        )

        evaluator.add_comparison(
            "m2",
            "Q2",
            "politics",
            {
                "fair_probability": 30.0,
                "action": "buy_no",
                "confidence": "medium",
                "edge_bps": -300,
            },
            {"fair_yes": 0.32, "rec": "buy no", "edge": -0.02},
        )

        evaluator.add_comparison(
            "m3",
            "Q3",
            "sports",
            {
                "fair_probability": 75.0,
                "action": "buy_yes",
                "confidence": "low",
                "edge_bps": 600,
            },
            {"fair_yes": 0.30, "rec": "buy no", "edge": -0.05},  # Disagreement
        )

        report = evaluator.generate_report()

        assert report.total_comparisons == 3
        assert report.llm_available_count == 3
        assert report.fallback_count == 0
        assert report.agreements == 2
        assert report.disagreements == 1

        # 2 out of 3 agree
        assert abs(report.agreement_rate - (2.0 / 3.0)) < 0.01

    def test_generate_report_avg_probability_delta(self):
        """Should calculate average absolute probability delta"""
        evaluator = LLMEvaluator()

        # Delta: +5
        evaluator.add_comparison(
            "m1",
            "Q1",
            "other",
            {
                "fair_probability": 65.0,
                "action": "avoid",
                "confidence": "medium",
                "edge_bps": 0,
            },
            {"fair_yes": 0.60, "rec": "avoid", "edge": 0.0},
        )

        # Delta: -10
        evaluator.add_comparison(
            "m2",
            "Q2",
            "other",
            {
                "fair_probability": 50.0,
                "action": "avoid",
                "confidence": "low",
                "edge_bps": 0,
            },
            {"fair_yes": 0.60, "rec": "avoid", "edge": 0.0},
        )

        # Delta: +15
        evaluator.add_comparison(
            "m3",
            "Q3",
            "other",
            {
                "fair_probability": 70.0,
                "action": "buy_yes",
                "confidence": "high",
                "edge_bps": 200,
            },
            {"fair_yes": 0.55, "rec": "buy yes", "edge": 0.01},
        )

        report = evaluator.generate_report()

        # Average of absolute deltas: (5 + 10 + 15) / 3 = 10.0
        assert abs(report.avg_probability_delta - 10.0) < 0.1

    def test_generate_report_breakdown_by_confidence(self):
        """Should break down statistics by confidence level"""
        evaluator = LLMEvaluator()

        # High confidence agreement
        evaluator.add_comparison(
            "m1",
            "Q1",
            "crypto",
            {
                "fair_probability": 70.0,
                "action": "buy_yes",
                "confidence": "high",
                "edge_bps": 600,
            },
            {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03},
        )

        # Medium confidence disagreement
        evaluator.add_comparison(
            "m2",
            "Q2",
            "politics",
            {
                "fair_probability": 75.0,
                "action": "buy_yes",
                "confidence": "medium",
                "edge_bps": 300,
            },
            {"fair_yes": 0.30, "rec": "buy no", "edge": -0.05},
        )

        # Low confidence agreement
        evaluator.add_comparison(
            "m3",
            "Q3",
            "sports",
            {
                "fair_probability": 50.0,
                "action": "avoid",
                "confidence": "low",
                "edge_bps": 0,
            },
            {"fair_yes": 0.51, "rec": "avoid", "edge": 0.0},
        )

        report = evaluator.generate_report()

        assert "high" in report.by_confidence
        assert "medium" in report.by_confidence
        assert "low" in report.by_confidence

        # High: 1 agreement
        assert report.by_confidence["high"]["count"] == 1
        assert report.by_confidence["high"]["agreement_rate"] == 1.0

        # Medium: 1 disagreement
        assert report.by_confidence["medium"]["count"] == 1
        assert report.by_confidence["medium"]["agreement_rate"] == 0.0

        # Low: 1 agreement
        assert report.by_confidence["low"]["count"] == 1
        assert report.by_confidence["low"]["agreement_rate"] == 1.0

    def test_generate_report_breakdown_by_category(self):
        """Should break down statistics by market category"""
        evaluator = LLMEvaluator()

        # Crypto: 2 comparisons, 1 agreement, 1 with LLM
        evaluator.add_comparison(
            "m1",
            "Q1",
            "crypto",
            {
                "fair_probability": 70.0,
                "action": "buy_yes",
                "confidence": "high",
                "edge_bps": 500,
            },
            {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03},
        )

        evaluator.add_comparison(
            "m2",
            "Q2",
            "crypto",
            {
                "fair_probability": 75.0,
                "action": "buy_yes",
                "confidence": "medium",
                "edge_bps": 600,
            },
            {"fair_yes": 0.30, "rec": "buy no", "edge": -0.05},
        )

        # Politics: 1 comparison, 1 agreement
        evaluator.add_comparison(
            "m3",
            "Q3",
            "politics",
            {
                "fair_probability": 50.0,
                "action": "avoid",
                "confidence": "low",
                "edge_bps": 0,
            },
            {"fair_yes": 0.51, "rec": "avoid", "edge": 0.0},
        )

        report = evaluator.generate_report()

        assert "crypto" in report.by_category
        assert "politics" in report.by_category

        # Crypto: 50% agreement
        assert report.by_category["crypto"]["count"] == 2
        assert report.by_category["crypto"]["llm_available"] == 2
        assert abs(report.by_category["crypto"]["agreement_rate"] - 0.5) < 0.01

        # Politics: 100% agreement
        assert report.by_category["politics"]["count"] == 1
        assert report.by_category["politics"]["llm_available"] == 1
        assert report.by_category["politics"]["agreement_rate"] == 1.0

    def test_calibration_score_high_alignment(self):
        """Should calculate high calibration score for aligned confidence-edge pairs"""
        evaluator = LLMEvaluator()

        # All with aligned confidence-edge pairs
        for i in range(10):
            evaluator.add_comparison(
                f"m{i}",
                f"Q{i}",
                "other",
                {
                    "fair_probability": 70.0,
                    "action": "buy_yes",
                    "confidence": "high",
                    "edge_bps": 600,  # High confidence with large edge = aligned
                },
                {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03},
            )

        report = evaluator.generate_report()

        # All aligned → high calibration score
        assert report.calibration_score == 1.0

    def test_calibration_score_poor_alignment(self):
        """Should calculate low calibration score for misaligned confidence-edge pairs"""
        evaluator = LLMEvaluator()

        # All misaligned: high confidence with small edges
        for i in range(10):
            evaluator.add_comparison(
                f"m{i}",
                f"Q{i}",
                "other",
                {
                    "fair_probability": 70.0,
                    "action": "buy_yes",
                    "confidence": "high",
                    "edge_bps": 100,  # High confidence with small edge = misaligned
                },
                {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03},
            )

        report = evaluator.generate_report()

        # All misaligned → low calibration score
        assert report.calibration_score == 0.0

    def test_export_report(self, tmp_path):
        """Should export evaluation report to JSON"""
        evaluator = LLMEvaluator()
        output_file = tmp_path / "eval_report.json"

        evaluator.add_comparison(
            "m1",
            "Q1",
            "crypto",
            {
                "fair_probability": 70.0,
                "action": "buy_yes",
                "confidence": "high",
                "edge_bps": 500,
            },
            {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03},
        )

        evaluator.export_report(output_file)

        # Should create file
        assert output_file.exists()

        # Should be valid JSON
        data = json.loads(output_file.read_text())

        assert "report" in data
        assert "detailed_comparisons" in data

        # Check report structure
        report = data["report"]
        assert "generated_at" in report
        assert "total_comparisons" in report
        assert "llm_available_count" in report
        assert "fallback_count" in report
        assert "agreement_rate" in report
        assert "agreements" in report
        assert "disagreements" in report

    def test_export_report_creates_directory(self, tmp_path):
        """Should create parent directories if needed"""
        evaluator = LLMEvaluator()
        output_file = tmp_path / "nested" / "dir" / "eval.json"

        evaluator.add_comparison(
            "m1",
            "Q1",
            "other",
            {
                "fair_probability": 50.0,
                "action": "avoid",
                "confidence": "low",
                "edge_bps": 0,
            },
            {"fair_yes": 0.50, "rec": "avoid", "edge": 0.0},
        )

        # Should not crash
        evaluator.export_report(output_file)

        assert output_file.exists()

    def test_export_includes_detailed_comparisons(self, tmp_path):
        """Exported report should include detailed comparison data"""
        evaluator = LLMEvaluator()
        output_file = tmp_path / "report.json"

        evaluator.add_comparison(
            "m1",
            "Q1",
            "crypto",
            {
                "fair_probability": 70.0,
                "action": "buy_yes",
                "confidence": "high",
                "edge_bps": 500,
            },
            {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03},
        )

        evaluator.add_comparison(
            "m2",
            "Q2",
            "politics",
            {
                "fair_probability": 30.0,
                "action": "buy_no",
                "confidence": "medium",
                "edge_bps": -300,
            },
            {"fair_yes": 0.32, "rec": "buy no", "edge": -0.02},
        )

        evaluator.export_report(output_file)

        data = json.loads(output_file.read_text())

        assert len(data["detailed_comparisons"]) == 2
        assert data["detailed_comparisons"][0]["market_id"] == "m1"
        assert data["detailed_comparisons"][1]["market_id"] == "m2"

    def test_comparison_with_none_llm_skipped_in_stats(self):
        """Comparisons with None LLM opinion should not affect agreement stats"""
        evaluator = LLMEvaluator()

        # Add one valid comparison
        evaluator.add_comparison(
            "m1",
            "Q1",
            "crypto",
            {
                "fair_probability": 70.0,
                "action": "buy_yes",
                "confidence": "high",
                "edge_bps": 500,
            },
            {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03},
        )

        # Add one with None LLM
        evaluator.add_comparison(
            "m2", "Q2", "politics", None, {"fair_yes": 0.50, "rec": "avoid", "edge": 0.0}
        )

        report = evaluator.generate_report()

        # Total comparisons includes both
        assert report.total_comparisons == 2

        # But only 1 has LLM available
        assert report.llm_available_count == 1
        assert report.fallback_count == 1

        # Agreement rate based only on LLM-available comparisons
        assert report.agreement_rate == 1.0
        assert report.agreements == 1
        assert report.disagreements == 0

    def test_evaluation_report_dataclass(self):
        """EvaluationReport should be a proper dataclass"""
        report = EvaluationReport(
            generated_at="2025-01-01T00:00:00Z",
            total_comparisons=10,
            llm_available_count=8,
            fallback_count=2,
            agreement_rate=0.75,
            agreements=6,
            disagreements=2,
            avg_probability_delta=5.0,
            avg_edge_delta_bps=100,
            calibration_score=0.85,
            by_confidence={},
            by_category={},
        )

        assert report.total_comparisons == 10
        assert report.llm_available_count == 8
        assert report.fallback_count == 2
        assert report.agreement_rate == 0.75
        assert report.agreements == 6
        assert report.disagreements == 2
        assert report.calibration_score == 0.85

    def test_comparison_dataclass(self):
        """Comparison should be a proper dataclass"""
        comparison = Comparison(
            market_id="test-1",
            market_question="Test?",
            market_category="crypto",
            llm_fair_probability=70.0,
            llm_edge_bps=500,
            llm_action="buy_yes",
            llm_confidence="high",
            naive_fair_probability=68.0,
            naive_edge_bps=300,
            naive_action="buy_yes",
            directional_agreement=True,
            probability_delta=2.0,
            edge_delta_bps=200,
            confidence_edge_alignment="aligned",
        )

        assert comparison.market_id == "test-1"
        assert comparison.llm_edge_bps == 500
        assert comparison.naive_edge_bps == 300
        assert comparison.directional_agreement is True
        assert comparison.probability_delta == 2.0
        assert comparison.edge_delta_bps == 200
        assert comparison.confidence_edge_alignment == "aligned"

    def test_large_evaluation_set_performance(self):
        """Should handle large number of comparisons efficiently"""
        evaluator = LLMEvaluator()

        # Add 1000 comparisons
        for i in range(1000):
            evaluator.add_comparison(
                f"m{i}",
                f"Q{i}",
                "crypto",
                {
                    "fair_probability": 60.0 + (i % 20),
                    "action": "buy_yes",
                    "confidence": "medium",
                    "edge_bps": 300,
                },
                {"fair_yes": 0.60 + (i % 20) * 0.01, "rec": "buy yes", "edge": 0.02},
            )

        report = evaluator.generate_report()

        assert report.total_comparisons == 1000
        assert report.llm_available_count == 1000

    def test_reset(self):
        """Should reset evaluator for new session"""
        evaluator = LLMEvaluator()

        evaluator.add_comparison(
            "m1",
            "Q1",
            "crypto",
            {
                "fair_probability": 70.0,
                "action": "buy_yes",
                "confidence": "high",
                "edge_bps": 500,
            },
            {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03},
        )

        assert len(evaluator.comparisons) == 1

        evaluator.reset()

        assert len(evaluator.comparisons) == 0

    def test_confidence_alignment_rate_in_by_confidence(self):
        """Should calculate confidence_alignment_rate in by_confidence breakdown"""
        evaluator = LLMEvaluator()

        # Add high confidence with aligned edge
        evaluator.add_comparison(
            "m1",
            "Q1",
            "crypto",
            {
                "fair_probability": 70.0,
                "action": "buy_yes",
                "confidence": "high",
                "edge_bps": 600,  # Aligned for high confidence
            },
            {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03},
        )

        # Add high confidence with misaligned edge
        evaluator.add_comparison(
            "m2",
            "Q2",
            "crypto",
            {
                "fair_probability": 70.0,
                "action": "buy_yes",
                "confidence": "high",
                "edge_bps": 100,  # Misaligned for high confidence
            },
            {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03},
        )

        report = evaluator.generate_report()

        # 1 out of 2 high confidence comparisons are aligned
        assert abs(report.by_confidence["high"]["confidence_alignment_rate"] - 0.5) < 0.01

    def test_by_category_with_fallback(self):
        """Should handle category stats when some comparisons have no LLM opinion"""
        evaluator = LLMEvaluator()

        # Crypto with LLM
        evaluator.add_comparison(
            "m1",
            "Q1",
            "crypto",
            {
                "fair_probability": 70.0,
                "action": "buy_yes",
                "confidence": "high",
                "edge_bps": 500,
            },
            {"fair_yes": 0.68, "rec": "buy yes", "edge": 0.03},
        )

        # Crypto without LLM
        evaluator.add_comparison(
            "m2", "Q2", "crypto", None, {"fair_yes": 0.50, "rec": "avoid", "edge": 0.0}
        )

        report = evaluator.generate_report()

        assert report.by_category["crypto"]["count"] == 2
        assert report.by_category["crypto"]["llm_available"] == 1
        assert report.by_category["crypto"]["agreement_rate"] == 1.0
