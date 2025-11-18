#!/usr/bin/env python3
"""
LLM Evaluation Framework

Compares LLM outputs against baseline (naive) model to evaluate:
- Directional agreement (do they agree on buy/sell/hold?)
- Edge delta (how much do probability estimates differ?)
- Calibration proxy (confidence vs edge magnitude)
- Confidence penalty (does high confidence correlate with large edges?)

Used to:
- Validate LLM is providing useful signal
- Tune confidence thresholds
- Decide whether to trust LLM over naive model

Usage:
    evaluator = LLMEvaluator()

    # Add comparisons
    evaluator.add_comparison(
        market_id="market-001",
        llm_opinion=llm_opinion,
        naive_opinion=naive_opinion,
    )

    # Generate report
    report = evaluator.generate_report()
    evaluator.export_report(Path("state/llm_evaluation_report.json"))
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


@dataclass
class Comparison:
    """Single market comparison between LLM and naive model"""
    market_id: str
    market_question: str
    market_category: str

    # LLM opinion
    llm_fair_probability: Optional[float]  # 0-100
    llm_edge_bps: Optional[int]
    llm_action: Optional[str]
    llm_confidence: Optional[str]

    # Naive opinion
    naive_fair_probability: float  # 0-100
    naive_edge_bps: int
    naive_action: str

    # Computed metrics
    directional_agreement: bool
    probability_delta: Optional[float]  # LLM - naive
    edge_delta_bps: Optional[int]       # LLM - naive
    confidence_edge_alignment: Optional[str]  # "aligned", "misaligned", "n/a"


@dataclass
class EvaluationReport:
    """Aggregated evaluation metrics"""
    generated_at: str
    total_comparisons: int
    llm_available_count: int
    fallback_count: int

    # Directional agreement
    agreement_rate: float  # 0-1
    agreements: int
    disagreements: int

    # Edge deltas
    avg_probability_delta: float  # Average |LLM - naive| probability
    avg_edge_delta_bps: float     # Average |LLM - naive| edge

    # By confidence
    by_confidence: Dict[str, Dict[str, Any]]

    # By category
    by_category: Dict[str, Dict[str, Any]]

    # Confidence calibration
    calibration_score: float  # 0-1, higher = better calibrated


class LLMEvaluator:
    """
    LLM Evaluation Framework

    Compares LLM opinions against naive baseline model.
    Tracks agreement, calibration, and edge differences.
    """

    def __init__(self):
        """Initialize evaluator"""
        self.comparisons: List[Comparison] = []

    def add_comparison(
        self,
        market_id: str,
        market_question: str,
        market_category: str,
        llm_opinion: Optional[Dict[str, Any]],
        naive_opinion: Dict[str, Any],
    ) -> None:
        """
        Add a comparison between LLM and naive opinions

        Args:
            market_id: Market identifier
            market_question: Market question
            market_category: Market category
            llm_opinion: LLM opinion dict (or None if unavailable)
            naive_opinion: Naive model opinion dict
        """
        # Extract LLM values
        if llm_opinion:
            llm_fair_prob = llm_opinion.get("fair_probability")
            llm_edge_bps = llm_opinion.get("edge_bps")
            llm_action = llm_opinion.get("action")
            llm_confidence = llm_opinion.get("confidence")
        else:
            llm_fair_prob = None
            llm_edge_bps = None
            llm_action = None
            llm_confidence = None

        # Extract naive values (convert from 0-1 to 0-100 if needed)
        naive_fair_prob = naive_opinion.get("fair_yes", 0.5) * 100
        naive_edge = naive_opinion.get("edge", 0.0) * 10000  # Convert to bps
        naive_action = self._normalize_action(naive_opinion.get("rec", "hold"))

        # Compute metrics
        directional_agreement = self._check_directional_agreement(
            llm_action, naive_action
        )

        probability_delta = None
        edge_delta_bps = None
        if llm_fair_prob is not None:
            probability_delta = llm_fair_prob - naive_fair_prob
            edge_delta_bps = llm_edge_bps - int(naive_edge)

        confidence_edge_alignment = self._check_confidence_alignment(
            llm_confidence, llm_edge_bps
        )

        # Create comparison
        comparison = Comparison(
            market_id=market_id,
            market_question=market_question,
            market_category=market_category,
            llm_fair_probability=llm_fair_prob,
            llm_edge_bps=llm_edge_bps,
            llm_action=llm_action,
            llm_confidence=llm_confidence,
            naive_fair_probability=naive_fair_prob,
            naive_edge_bps=int(naive_edge),
            naive_action=naive_action,
            directional_agreement=directional_agreement,
            probability_delta=probability_delta,
            edge_delta_bps=edge_delta_bps,
            confidence_edge_alignment=confidence_edge_alignment,
        )

        self.comparisons.append(comparison)

    def _normalize_action(self, action: str) -> str:
        """Normalize action string to standard format"""
        action = str(action).lower().replace(" ", "_")
        if action in ["buy_yes", "buy yes"]:
            return "buy_yes"
        elif action in ["buy_no", "buy no"]:
            return "buy_no"
        else:
            return "avoid"

    def _check_directional_agreement(
        self,
        llm_action: Optional[str],
        naive_action: str,
    ) -> bool:
        """Check if LLM and naive agree on direction"""
        if llm_action is None:
            return False
        return llm_action == naive_action

    def _check_confidence_alignment(
        self,
        confidence: Optional[str],
        edge_bps: Optional[int],
    ) -> Optional[str]:
        """
        Check if confidence aligns with edge magnitude

        High confidence should correspond to large edges.
        Low confidence should correspond to small edges.
        """
        if confidence is None or edge_bps is None:
            return None

        abs_edge = abs(edge_bps)

        # Define thresholds
        # high confidence should have edge > 500 bps
        # medium confidence: 200-500 bps
        # low confidence: < 200 bps

        if confidence == "high":
            return "aligned" if abs_edge > 500 else "misaligned"
        elif confidence == "medium":
            return "aligned" if 200 <= abs_edge <= 800 else "misaligned"
        elif confidence == "low":
            return "aligned" if abs_edge < 400 else "misaligned"

        return None

    def generate_report(self) -> EvaluationReport:
        """
        Generate aggregated evaluation report

        Returns:
            EvaluationReport with all metrics
        """
        total = len(self.comparisons)

        if total == 0:
            return EvaluationReport(
                generated_at=datetime.now(timezone.utc).isoformat(),
                total_comparisons=0,
                llm_available_count=0,
                fallback_count=0,
                agreement_rate=0.0,
                agreements=0,
                disagreements=0,
                avg_probability_delta=0.0,
                avg_edge_delta_bps=0.0,
                by_confidence={},
                by_category={},
                calibration_score=0.0,
            )

        # Count LLM vs fallback
        llm_available = sum(1 for c in self.comparisons if c.llm_action is not None)
        fallback = total - llm_available

        # Directional agreement (only for markets where LLM available)
        agreements = sum(1 for c in self.comparisons if c.directional_agreement)
        disagreements = llm_available - agreements
        agreement_rate = agreements / llm_available if llm_available > 0 else 0.0

        # Edge deltas (only where LLM available)
        prob_deltas = [abs(c.probability_delta) for c in self.comparisons if c.probability_delta is not None]
        edge_deltas = [abs(c.edge_delta_bps) for c in self.comparisons if c.edge_delta_bps is not None]

        avg_prob_delta = sum(prob_deltas) / len(prob_deltas) if prob_deltas else 0.0
        avg_edge_delta = sum(edge_deltas) / len(edge_deltas) if edge_deltas else 0.0

        # By confidence
        by_confidence = self._aggregate_by_confidence()

        # By category
        by_category = self._aggregate_by_category()

        # Calibration score
        calibration_score = self._compute_calibration_score()

        return EvaluationReport(
            generated_at=datetime.now(timezone.utc).isoformat(),
            total_comparisons=total,
            llm_available_count=llm_available,
            fallback_count=fallback,
            agreement_rate=agreement_rate,
            agreements=agreements,
            disagreements=disagreements,
            avg_probability_delta=avg_prob_delta,
            avg_edge_delta_bps=avg_edge_delta,
            by_confidence=by_confidence,
            by_category=by_category,
            calibration_score=calibration_score,
        )

    def _aggregate_by_confidence(self) -> Dict[str, Dict[str, Any]]:
        """Aggregate metrics by confidence level"""
        by_conf: Dict[str, List[Comparison]] = {
            "high": [],
            "medium": [],
            "low": [],
        }

        for comp in self.comparisons:
            if comp.llm_confidence:
                by_conf[comp.llm_confidence].append(comp)

        result = {}
        for conf, comps in by_conf.items():
            if not comps:
                continue

            agreements = sum(1 for c in comps if c.directional_agreement)
            avg_edge = sum(abs(c.edge_delta_bps) for c in comps if c.edge_delta_bps is not None)
            avg_edge = avg_edge / len([c for c in comps if c.edge_delta_bps is not None]) if any(c.edge_delta_bps is not None for c in comps) else 0

            aligned = sum(1 for c in comps if c.confidence_edge_alignment == "aligned")
            total_with_alignment = sum(1 for c in comps if c.confidence_edge_alignment is not None)

            result[conf] = {
                "count": len(comps),
                "agreement_rate": agreements / len(comps),
                "avg_edge_delta_bps": avg_edge,
                "confidence_alignment_rate": aligned / total_with_alignment if total_with_alignment > 0 else 0.0,
            }

        return result

    def _aggregate_by_category(self) -> Dict[str, Dict[str, Any]]:
        """Aggregate metrics by market category"""
        by_cat: Dict[str, List[Comparison]] = {}

        for comp in self.comparisons:
            if comp.market_category not in by_cat:
                by_cat[comp.market_category] = []
            by_cat[comp.market_category].append(comp)

        result = {}
        for cat, comps in by_cat.items():
            llm_available = sum(1 for c in comps if c.llm_action is not None)
            agreements = sum(1 for c in comps if c.directional_agreement)

            result[cat] = {
                "count": len(comps),
                "llm_available": llm_available,
                "agreement_rate": agreements / llm_available if llm_available > 0 else 0.0,
            }

        return result

    def _compute_calibration_score(self) -> float:
        """
        Compute calibration score

        High confidence should correlate with:
        - Large edges
        - High agreement with naive model (or strong signal)

        Returns value 0-1, higher = better calibrated
        """
        # Filter to only LLM-available comparisons
        llm_comps = [c for c in self.comparisons if c.llm_confidence is not None]

        if not llm_comps:
            return 0.0

        # Count aligned confidence-edge pairs
        aligned = sum(1 for c in llm_comps if c.confidence_edge_alignment == "aligned")

        # Calibration = % of confidence levels that align with edge magnitude
        return aligned / len(llm_comps)

    def export_report(self, output_path: Path) -> None:
        """
        Export evaluation report to JSON file

        Args:
            output_path: Path to write JSON report
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate report
        report = self.generate_report()

        # Build full export
        export = {
            "report": asdict(report),
            "detailed_comparisons": [asdict(c) for c in self.comparisons],
        }

        # Write JSON
        output_path.write_text(json.dumps(export, indent=2), encoding="utf-8")

    def reset(self) -> None:
        """Reset evaluator for new session"""
        self.comparisons = []
