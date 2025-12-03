#!/usr/bin/env python3
"""
Batch 22: Consensus Feedback Engine
Runs multiple agents and computes consensus feedback.

Multi-agent consensus system that:
- Runs rules engine, LLM agents, and heuristics
- Computes agreement scores and stability
- Detects contradictions
- Generates final recommendations
"""

import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence levels for consensus."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SeverityLevel(Enum):
    """Severity levels for issues."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AgentResponse:
    """Response from a consensus agent."""
    agent_name: str
    recommendations: List[str] = field(default_factory=list)
    priority_items: List[Dict] = field(default_factory=list)
    confidence: float = 0.5
    severity_assessment: str = "medium"
    notes: List[str] = field(default_factory=list)


@dataclass
class ConsensusOutput:
    """Final consensus output."""
    agreement_score: float = 0.0
    confidence: str = "medium"
    stability_score: float = 0.0
    priority_items: List[Dict] = field(default_factory=list)
    contradictions: List[Dict] = field(default_factory=list)
    final_recommendations: List[str] = field(default_factory=list)


class ConsensusEngine:
    """
    Multi-agent consensus engine for system feedback analysis.

    Runs multiple analysis agents and computes consensus on:
    - Issue severity
    - Recommended actions
    - System health assessment
    """

    def __init__(
        self,
        feedback_path: str = None,
        output_path: str = None,
        verbose: bool = False
    ):
        self.feedback_path = feedback_path
        self.output_path = output_path
        self.verbose = verbose
        self.feedback_data: Dict = {"issues": [], "metrics": {}}
        self.agent_responses: List[AgentResponse] = []
        self.errors: List[str] = []

    def load_feedback(self) -> bool:
        """Load feedback data from file."""
        if not self.feedback_path:
            self.errors.append("Feedback path not specified")
            return False

        path = Path(self.feedback_path)
        if not path.exists():
            self.errors.append(f"Feedback file not found: {self.feedback_path}")
            self.feedback_data = {"issues": [], "metrics": {}}
            return False

        try:
            with open(path, 'r') as f:
                content = f.read()
                self.feedback_data = json.loads(content)
            return True
        except json.JSONDecodeError as e:
            self.errors.append(f"Malformed JSON in feedback file: {e}")
            self.feedback_data = {"issues": [], "metrics": {}}
            return False
        except Exception as e:
            self.errors.append(f"Error loading feedback: {e}")
            self.feedback_data = {"issues": [], "metrics": {}}
            return False

    def run_rules_engine(self) -> AgentResponse:
        """Run deterministic rules-based analysis."""
        issues = self.feedback_data.get("issues", [])
        metrics = self.feedback_data.get("metrics", {})

        recommendations = []
        priority_items = []
        severity = "low"
        confidence = 0.9

        # Analyze issues by severity
        critical_count = sum(1 for i in issues if i.get("severity") == "critical")
        high_count = sum(1 for i in issues if i.get("severity") == "high")
        medium_count = sum(1 for i in issues if i.get("severity") == "medium")

        if critical_count > 0:
            severity = "critical"
            recommendations.append("Immediate attention required for critical issues")
            for i, issue in enumerate(issues):
                if issue.get("severity") == "critical":
                    priority_items.append({
                        "source_agent": "rules_engine",
                        "priority": 1,
                        "description": issue.get("type", f"Critical issue {i}")
                    })
        elif high_count > 0:
            severity = "high"
            recommendations.append("Review high severity issues promptly")
            for i, issue in enumerate(issues):
                if issue.get("severity") == "high":
                    priority_items.append({
                        "source_agent": "rules_engine",
                        "priority": 2,
                        "description": issue.get("type", f"High severity issue {i}")
                    })
        elif medium_count > 0:
            severity = "medium"
            recommendations.append("Address medium severity issues in next cycle")
        else:
            recommendations.append("System appears healthy, continue monitoring")

        # Check error rate
        error_rate = metrics.get("error_rate", 0)
        if error_rate > 0.1:
            recommendations.append(f"Error rate {error_rate*100:.1f}% exceeds threshold")
            confidence = 0.95

        if not recommendations:
            recommendations.append("No specific recommendations")

        return AgentResponse(
            agent_name="rules_engine",
            recommendations=recommendations,
            priority_items=priority_items,
            confidence=confidence,
            severity_assessment=severity,
            notes=["Deterministic rules-based analysis"]
        )

    def run_llm_agent_1(self) -> AgentResponse:
        """Run conservative LLM agent (stubbed)."""
        issues = self.feedback_data.get("issues", [])

        recommendations = []
        priority_items = []

        if len(issues) > 0:
            recommendations.append("Thorough review recommended before changes")
            recommendations.append("Incremental fixes preferred over batch updates")
            for i, issue in enumerate(issues):
                priority_items.append({
                    "source_agent": "llm_agent_1_conservative",
                    "priority": i + 2,
                    "description": f"Review: {issue.get('type', 'issue')}"
                })
        else:
            recommendations.append("System stable, maintain current approach")

        severity = "high" if any(i.get("severity") == "critical" for i in issues) else "medium"

        return AgentResponse(
            agent_name="llm_agent_1_conservative",
            recommendations=recommendations,
            priority_items=priority_items,
            confidence=0.75,
            severity_assessment=severity,
            notes=["Conservative agent - prefers caution"]
        )

    def run_llm_agent_2(self) -> AgentResponse:
        """Run optimistic LLM agent (stubbed)."""
        issues = self.feedback_data.get("issues", [])

        recommendations = []
        priority_items = []

        if len(issues) > 0:
            recommendations.append("Batch processing of fixes recommended")
            recommendations.append("Quick parallel resolution possible")
            for i, issue in enumerate(issues):
                priority_items.append({
                    "source_agent": "llm_agent_2_optimistic",
                    "priority": i + 3,
                    "description": f"Fix quickly: {issue.get('type', 'issue')}"
                })
        else:
            recommendations.append("System optimal, consider scaling up")

        severity = "medium" if any(i.get("severity") in ["critical", "high"] for i in issues) else "low"

        return AgentResponse(
            agent_name="llm_agent_2_optimistic",
            recommendations=recommendations,
            priority_items=priority_items,
            confidence=0.8,
            severity_assessment=severity,
            notes=["Optimistic agent - prefers action"]
        )

    def run_heuristics(self) -> AgentResponse:
        """Run heuristics-based analysis."""
        issues = self.feedback_data.get("issues", [])
        metrics = self.feedback_data.get("metrics", {})

        recommendations = []
        priority_items = []

        # Simple heuristics
        if len(issues) > 5:
            recommendations.append("High issue count - prioritize triage")
            severity = "high"
        elif len(issues) > 2:
            recommendations.append("Moderate issues - scheduled review")
            severity = "medium"
        else:
            recommendations.append("Low issue count - system healthy")
            severity = "low"

        for i, issue in enumerate(issues[:3]):  # Top 3 only
            priority_items.append({
                "source_agent": "heuristics",
                "priority": i + 1,
                "description": f"Heuristic priority: {issue.get('type', 'issue')}"
            })

        return AgentResponse(
            agent_name="heuristics",
            recommendations=recommendations,
            priority_items=priority_items,
            confidence=0.85,
            severity_assessment=severity,
            notes=["Pattern-based heuristic analysis"]
        )

    def _confidence_to_bucket(self, confidence: float) -> str:
        """Convert confidence score to bucket."""
        if confidence >= 0.8:
            return "high"
        elif confidence >= 0.6:
            return "medium"
        else:
            return "low"

    def _compute_agreement_score(self) -> float:
        """Compute agreement score across agents."""
        if len(self.agent_responses) <= 1:
            return 1.0

        # Compare severity assessments
        severities = [r.severity_assessment for r in self.agent_responses]
        severity_agreement = len(set(severities)) / len(severities)
        severity_score = 1.0 - (severity_agreement - 1/len(severities))

        # Compare confidence levels
        confidences = [r.confidence for r in self.agent_responses]
        confidence_variance = max(confidences) - min(confidences)
        confidence_score = 1.0 - confidence_variance

        # Weighted average
        agreement = (severity_score * 0.6 + confidence_score * 0.4)
        return max(0.0, min(1.0, agreement))

    def _detect_contradictions(self) -> List[Dict]:
        """Detect contradictions between agents."""
        contradictions = []

        if len(self.agent_responses) < 2:
            return contradictions

        # Check severity contradictions
        severities = {r.agent_name: r.severity_assessment for r in self.agent_responses}
        severity_values = list(severities.values())

        if "critical" in severity_values and "low" in severity_values:
            contradictions.append({
                "type": "severity_mismatch",
                "description": "Agents disagree significantly on severity (critical vs low)"
            })
        elif "high" in severity_values and "low" in severity_values:
            contradictions.append({
                "type": "severity_mismatch",
                "description": "Agents disagree on severity (high vs low)"
            })

        return contradictions

    def _merge_priority_items(self) -> List[Dict]:
        """Merge priority items from all agents."""
        all_items = []
        for response in self.agent_responses:
            all_items.extend(response.priority_items)

        # Sort by priority
        all_items.sort(key=lambda x: x.get("priority", 999))
        return all_items

    def _generate_final_recommendations(self) -> List[str]:
        """Generate final recommendations based on consensus."""
        all_recs = []
        for response in self.agent_responses:
            all_recs.extend(response.recommendations)

        if not all_recs:
            return ["Continue monitoring system health"]

        # Deduplicate and return top recommendations
        seen = set()
        unique_recs = []
        for rec in all_recs:
            rec_lower = rec.lower()
            if rec_lower not in seen:
                seen.add(rec_lower)
                unique_recs.append(rec)

        return unique_recs[:5]

    def compute_consensus(self) -> ConsensusOutput:
        """Compute final consensus from all agent responses."""
        agreement_score = self._compute_agreement_score()

        # Compute average confidence
        if self.agent_responses:
            avg_confidence = sum(r.confidence for r in self.agent_responses) / len(self.agent_responses)
        else:
            avg_confidence = 0.5

        # Compute stability score
        stability_score = agreement_score * avg_confidence

        return ConsensusOutput(
            agreement_score=agreement_score,
            confidence=self._confidence_to_bucket(avg_confidence),
            stability_score=stability_score,
            priority_items=self._merge_priority_items(),
            contradictions=self._detect_contradictions(),
            final_recommendations=self._generate_final_recommendations()
        )

    def run(self) -> bool:
        """Run full consensus pipeline."""
        # Load feedback
        self.load_feedback()

        # Run all agents
        self.agent_responses = [
            self.run_rules_engine(),
            self.run_llm_agent_1(),
            self.run_llm_agent_2(),
            self.run_heuristics()
        ]

        # Compute consensus
        consensus = self.compute_consensus()

        # Build output
        output = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": self.feedback_path or "unknown",
            "agents": {
                r.agent_name: {
                    "recommendations": r.recommendations,
                    "priority_items": r.priority_items,
                    "confidence": r.confidence,
                    "severity_assessment": r.severity_assessment,
                    "notes": r.notes
                }
                for r in self.agent_responses
            },
            "consensus": {
                "agreement_score": consensus.agreement_score,
                "confidence": consensus.confidence,
                "stability_score": consensus.stability_score,
                "priority_items": consensus.priority_items,
                "contradictions": consensus.contradictions,
                "final_recommendations": consensus.final_recommendations
            },
            "issues_detected": self.feedback_data.get("issues", []),
            "notes": ["Multi-agent consensus analysis complete"],
            "errors": self.errors
        }

        # Write output
        if self.output_path:
            output_path = Path(self.output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(output, f, indent=2)

        return True


def run_consensus(state_dir: Path = Path("state")) -> Dict[str, Any]:
    """
    Run consensus engine on feedback.

    Args:
        state_dir: Directory where state files are stored

    Returns:
        Dict with status info
    """
    state_dir = Path(state_dir)
    feedback_path = state_dir / "brain_feedback.json"
    output_path = state_dir / "brain_consensus.json"

    engine = ConsensusEngine(
        feedback_path=str(feedback_path),
        output_path=str(output_path),
        verbose=False
    )

    success = engine.run()

    return {
        "status": "ok" if success else "error",
        "output_files": [str(output_path)]
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Consensus Feedback Engine")
    parser.add_argument("--input", "-i", help="Input feedback file path")
    parser.add_argument("--output", "-o", help="Output consensus file path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    if args.input and args.output:
        engine = ConsensusEngine(
            feedback_path=args.input,
            output_path=args.output,
            verbose=args.verbose
        )
        success = engine.run()
        if args.verbose:
            print(f"Consensus generated: {args.output}")
        exit(0 if success else 1)
    else:
        # Default behavior
        import sys
        state_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("state")
        result = run_consensus(state_dir)
        print(f"Consensus generated: {result}")
