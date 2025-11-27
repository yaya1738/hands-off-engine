#!/usr/bin/env python3
"""
Tests for the Autonomous Harmony System components.

Tests:
1. HarmonyOrchestrator - Domain health checks and coordination
2. SelfImprovementEngine - Software self-improvement detection
3. AlphaSelfLearningEngine - Trading strategy learning
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest import TestCase, main
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestHarmonyOrchestrator(TestCase):
    """Tests for the Harmony Orchestrator."""

    def test_import(self):
        """Test that HarmonyOrchestrator can be imported."""
        from scripts.harmony_orchestrator import (
            HarmonyOrchestrator, Domain, Priority, DomainHealth
        )
        self.assertIsNotNone(HarmonyOrchestrator)
        self.assertEqual(Domain.MONEY.value, "money")
        self.assertEqual(Domain.SOFTWARE.value, "software")
        self.assertEqual(Domain.HARDWARE.value, "hardware")

    def test_domain_health_creation(self):
        """Test creating DomainHealth objects."""
        from scripts.harmony_orchestrator import DomainHealth, Domain

        health = DomainHealth(
            domain=Domain.MONEY.value,
            status="healthy",
            score=0.95,
            metrics={"test": 1},
            last_check=datetime.now(timezone.utc).isoformat(),
            issues=[]
        )

        self.assertEqual(health.domain, "money")
        self.assertEqual(health.status, "healthy")
        self.assertGreater(health.score, 0.9)

        # Test serialization
        d = health.to_dict()
        self.assertIn("domain", d)
        self.assertIn("score", d)

    def test_harmony_score_calculation(self):
        """Test harmony score weighted calculation."""
        from scripts.harmony_orchestrator import (
            HarmonyOrchestrator, DomainHealth, Domain
        )

        orchestrator = HarmonyOrchestrator()

        money = DomainHealth(
            domain=Domain.MONEY.value,
            status="healthy",
            score=1.0,
            metrics={},
            last_check="",
            issues=[]
        )
        software = DomainHealth(
            domain=Domain.SOFTWARE.value,
            status="healthy",
            score=1.0,
            metrics={},
            last_check="",
            issues=[]
        )
        hardware = DomainHealth(
            domain=Domain.HARDWARE.value,
            status="healthy",
            score=1.0,
            metrics={},
            last_check="",
            issues=[]
        )

        score = orchestrator.calculate_harmony_score(money, software, hardware)
        self.assertEqual(score, 1.0)

        # Test with degraded money (most weight)
        money.score = 0.5
        score = orchestrator.calculate_harmony_score(money, software, hardware)
        # 0.5 * 0.5 (money) + 1.0 * 0.3 (software) + 1.0 * 0.2 (hardware) = 0.75
        self.assertAlmostEqual(score, 0.75, places=2)

    def test_improvement_identification(self):
        """Test that improvements are identified correctly."""
        from scripts.harmony_orchestrator import (
            HarmonyOrchestrator, DomainHealth, Domain
        )

        orchestrator = HarmonyOrchestrator()

        money = DomainHealth(
            domain=Domain.MONEY.value,
            status="degraded",
            score=0.7,
            metrics={},
            last_check="",
            issues=["Alpha model stale (25h old)"]
        )
        software = DomainHealth(
            domain=Domain.SOFTWARE.value,
            status="healthy",
            score=1.0,
            metrics={},
            last_check="",
            issues=[]
        )
        hardware = DomainHealth(
            domain=Domain.HARDWARE.value,
            status="healthy",
            score=1.0,
            metrics={},
            last_check="",
            issues=[]
        )

        improvements = orchestrator.identify_improvements(money, software, hardware)
        self.assertGreater(len(improvements), 0)
        self.assertEqual(improvements[0]["domain"], "money")


class TestSelfImprovementEngine(TestCase):
    """Tests for the Self-Improvement Engine."""

    def test_import(self):
        """Test that SelfImprovementEngine can be imported."""
        from scripts.self_improvement_engine import (
            SelfImprovementEngine, ImprovementOpportunity, ImprovementAction
        )
        self.assertIsNotNone(SelfImprovementEngine)

    def test_opportunity_creation(self):
        """Test creating improvement opportunities."""
        from scripts.self_improvement_engine import ImprovementOpportunity

        opp = ImprovementOpportunity(
            id="test_001",
            category="error_pattern",
            description="Recurring ImportError",
            source_file=None,
            severity="medium",
            auto_fixable=False,
            fix_suggestion="Check imports",
            discovered_at=datetime.now(timezone.utc).isoformat()
        )

        self.assertEqual(opp.category, "error_pattern")
        self.assertFalse(opp.auto_fixable)

        # Test serialization
        d = opp.to_dict()
        self.assertIn("id", d)
        self.assertIn("category", d)

    def test_prioritization(self):
        """Test opportunity prioritization."""
        from scripts.self_improvement_engine import (
            SelfImprovementEngine, ImprovementOpportunity
        )

        engine = SelfImprovementEngine()

        opps = [
            ImprovementOpportunity(
                id="1", category="code_quality", description="Low",
                source_file=None, severity="low", auto_fixable=False,
                fix_suggestion="", discovered_at=""
            ),
            ImprovementOpportunity(
                id="2", category="error_pattern", description="High",
                source_file=None, severity="high", auto_fixable=True,
                fix_suggestion="", discovered_at=""
            ),
        ]

        prioritized = engine.prioritize_opportunities(opps)
        # Error pattern with high severity and auto-fixable should be first
        self.assertEqual(prioritized[0].id, "2")


class TestAlphaSelfLearningEngine(TestCase):
    """Tests for the Alpha Self-Learning Engine."""

    def test_import(self):
        """Test that AlphaSelfLearningEngine can be imported."""
        from alpha.alpha_self_learning import (
            AlphaSelfLearningEngine, TradeOutcome, LearningInsight
        )
        self.assertIsNotNone(AlphaSelfLearningEngine)

    def test_trade_outcome_creation(self):
        """Test creating trade outcomes."""
        from alpha.alpha_self_learning import TradeOutcome

        outcome = TradeOutcome(
            trade_id="trade_001",
            market_id="market_001",
            market_name="Test Market",
            side="YES",
            predicted_edge=0.05,
            actual_outcome="win",
            predicted_confidence=0.8,
            entry_price=0.6,
            exit_price=1.0,
            pnl=10.0,
            timestamp=datetime.now(timezone.utc).isoformat()
        )

        self.assertEqual(outcome.side, "YES")
        self.assertEqual(outcome.actual_outcome, "win")
        self.assertGreater(outcome.pnl, 0)

    def test_learning_insight_creation(self):
        """Test creating learning insights."""
        from alpha.alpha_self_learning import LearningInsight

        insight = LearningInsight(
            insight_type="overconfidence",
            description="High confidence trades underperforming",
            adjustment_suggested={"confidence_bias": -0.05},
            confidence=0.7,
            based_on_trades=50,
            discovered_at=datetime.now(timezone.utc).isoformat()
        )

        self.assertEqual(insight.insight_type, "overconfidence")
        self.assertIn("confidence_bias", insight.adjustment_suggested)

    def test_performance_metrics(self):
        """Test performance metrics calculation."""
        from alpha.alpha_self_learning import AlphaSelfLearningEngine, TradeOutcome

        engine = AlphaSelfLearningEngine()

        # Add some test outcomes
        for i in range(10):
            outcome = TradeOutcome(
                trade_id=f"trade_{i}",
                market_id=f"market_{i}",
                market_name="Test",
                side="YES",
                predicted_edge=0.05,
                actual_outcome="win" if i < 6 else "loss",
                predicted_confidence=0.75,
                entry_price=0.5,
                exit_price=1.0 if i < 6 else 0.0,
                pnl=10.0 if i < 6 else -10.0,
                timestamp=""
            )
            engine.outcomes.append(outcome)

        metrics = engine.calculate_performance_metrics()
        self.assertEqual(metrics["trades"], 10)
        self.assertEqual(metrics["wins"], 6)
        self.assertAlmostEqual(metrics["win_rate"], 0.6, places=2)

    def test_get_current_biases(self):
        """Test getting current model biases."""
        from alpha.alpha_self_learning import AlphaSelfLearningEngine

        engine = AlphaSelfLearningEngine()
        biases = engine.get_current_biases()

        self.assertIn("confidence_bias", biases)
        self.assertIn("min_edge_threshold", biases)
        self.assertIn("kelly_fraction_cap", biases)


class TestIntegration(TestCase):
    """Integration tests for the harmony system."""

    def test_full_harmony_cycle(self):
        """Test running a full harmony cycle."""
        from scripts.harmony_orchestrator import HarmonyOrchestrator

        orchestrator = HarmonyOrchestrator()
        state = orchestrator.run_cycle()

        self.assertIsNotNone(state)
        self.assertGreaterEqual(state.overall_health, 0.0)
        self.assertLessEqual(state.overall_health, 1.0)
        self.assertIn(state.mode, ["normal", "optimization", "maintenance"])

    def test_self_improvement_cycle(self):
        """Test running a self-improvement cycle."""
        from scripts.self_improvement_engine import SelfImprovementEngine

        engine = SelfImprovementEngine()
        report = engine.run_cycle()

        self.assertIn("total_opportunities", report)
        self.assertIn("by_category", report)
        self.assertIn("opportunities", report)

    def test_alpha_learning_cycle(self):
        """Test running an alpha learning cycle."""
        from alpha.alpha_self_learning import AlphaSelfLearningEngine

        engine = AlphaSelfLearningEngine()
        report = engine.run_learning_cycle(apply_changes=False)

        self.assertIn("metrics", report)
        self.assertIn("insights", report)
        self.assertIn("adjustments_proposed", report)
        self.assertEqual(report["mode"], "dry_run")


if __name__ == '__main__':
    main()
