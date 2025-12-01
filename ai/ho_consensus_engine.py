#!/usr/bin/env python3
"""
Hands-Off Engine - Batch 22: Consensus Feedback Engine

Multi-agent reasoning layer that aggregates feedback from multiple sources
and produces consensus-weighted guidance for the Policy Brain.

SAFETY:
- DRYRUN only - no execution
- No network calls
- No real LLM API calls (uses deterministic mocks)
- File operations only in state/
- Pure cognition, not execution

Author: Hands-Off Engine Team
Batch: 22
"""

import json
import sys
import os
import argparse
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence bucket classification"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SeverityLevel(Enum):
    """Issue severity classification"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class AgentResponse:
    """Response from a single agent"""
    agent_name: str
    recommendations: List[str]
    priority_items: List[Dict[str, Any]]
    confidence: float  # 0.0 to 1.0
    severity_assessment: str
    notes: List[str]


@dataclass
class ConsensusOutput:
    """Final consensus output structure"""
    generated_at: str
    source: str
    agents: Dict[str, Dict[str, Any]]
    consensus: Dict[str, Any]
    issues_detected: List[Dict[str, Any]]
    notes: List[str]
    errors: List[str]


class ConsensusEngine:
    """
    Multi-agent consensus engine for feedback aggregation.

    This engine:
    1. Loads feedback from brain_feedback.json
    2. Runs multiple reasoning agents (mocked, deterministic)
    3. Computes consensus scores and recommendations
    4. Outputs structured consensus to brain_consensus.json
    """

    def __init__(self,
                 feedback_path: str = "state/brain_feedback.json",
                 output_path: str = "state/brain_consensus.json",
                 verbose: bool = False):
        """
        Initialize the consensus engine.

        Args:
            feedback_path: Path to input brain_feedback.json
            output_path: Path to output brain_consensus.json
            verbose: Enable verbose output
        """
        self.feedback_path = feedback_path
        self.output_path = output_path
        self.verbose = verbose
        self.feedback_data: Optional[Dict[str, Any]] = None
        self.agent_responses: List[AgentResponse] = []
        self.errors: List[str] = []
        self.notes: List[str] = []

    def log(self, message: str) -> None:
        """Log message if verbose mode enabled"""
        if self.verbose:
            print(f"[ConsensusEngine] {message}")

    def load_feedback(self) -> bool:
        """
        Load brain_feedback.json with robust error handling.

        Returns:
            True if loaded successfully, False otherwise
        """
        self.log(f"Loading feedback from: {self.feedback_path}")

        if not os.path.exists(self.feedback_path):
            error_msg = f"Feedback file not found: {self.feedback_path}"
            self.errors.append(error_msg)
            self.log(f"ERROR: {error_msg}")
            # Create minimal empty feedback
            self.feedback_data = {"issues": [], "metrics": {}}
            return False

        try:
            with open(self.feedback_path, 'r') as f:
                self.feedback_data = json.load(f)

            # Validate basic structure
            if not isinstance(self.feedback_data, dict):
                raise ValueError("Feedback must be a JSON object")

            self.log(f"Successfully loaded feedback with {len(self.feedback_data.get('issues', []))} issues")
            return True

        except json.JSONDecodeError as e:
            error_msg = f"Malformed JSON in feedback file: {e}"
            self.errors.append(error_msg)
            self.log(f"ERROR: {error_msg}")
            self.feedback_data = {"issues": [], "metrics": {}}
            return False

        except Exception as e:
            error_msg = f"Error loading feedback: {e}"
            self.errors.append(error_msg)
            self.log(f"ERROR: {error_msg}")
            self.feedback_data = {"issues": [], "metrics": {}}
            return False

    def run_rules_engine(self) -> AgentResponse:
        """
        Rules-based agent: applies deterministic heuristics.

        This agent uses hard-coded rules to evaluate feedback:
        - Count issues by severity
        - Flag critical patterns
        - Apply threshold-based priorities

        Returns:
            AgentResponse from rules engine
        """
        self.log("Running rules engine agent...")

        issues = self.feedback_data.get('issues', [])
        metrics = self.feedback_data.get('metrics', {})

        recommendations = []
        priority_items = []
        notes = []

        # Rule 1: Count severity levels
        severity_counts = {}
        for issue in issues:
            sev = issue.get('severity', 'unknown')
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        # Rule 2: Critical threshold
        critical_count = severity_counts.get('critical', 0)
        if critical_count > 0:
            recommendations.append(f"Address {critical_count} critical issue(s) immediately")
            priority_items.append({
                "type": "critical_issues",
                "count": critical_count,
                "priority": 1
            })
            notes.append(f"Rules engine flagged {critical_count} critical issues")

        # Rule 3: High severity threshold
        high_count = severity_counts.get('high', 0)
        if high_count > 2:
            recommendations.append(f"Review {high_count} high-severity issues")
            priority_items.append({
                "type": "high_severity_issues",
                "count": high_count,
                "priority": 2
            })

        # Rule 4: Error rate check
        error_rate = metrics.get('error_rate', 0)
        if error_rate > 0.1:  # 10% threshold
            recommendations.append(f"Error rate {error_rate:.1%} exceeds threshold")
            priority_items.append({
                "type": "high_error_rate",
                "value": error_rate,
                "priority": 1
            })

        # Rule 5: No issues detected
        if len(issues) == 0:
            recommendations.append("No issues detected - system healthy")
            notes.append("Rules engine: clean state")

        # Determine confidence based on data quality
        confidence = 0.9 if len(issues) > 0 else 0.7

        # Determine severity
        if critical_count > 0:
            severity = SeverityLevel.CRITICAL.value
        elif high_count > 0:
            severity = SeverityLevel.HIGH.value
        elif len(issues) > 0:
            severity = SeverityLevel.MEDIUM.value
        else:
            severity = SeverityLevel.LOW.value

        return AgentResponse(
            agent_name="rules_engine",
            recommendations=recommendations,
            priority_items=priority_items,
            confidence=confidence,
            severity_assessment=severity,
            notes=notes
        )

    def run_llm_agent_1(self) -> AgentResponse:
        """
        Mocked LLM Agent #1: Conservative, safety-focused reasoning.

        This agent simulates an LLM with conservative bias:
        - Prioritizes safety and risk mitigation
        - Prefers incremental changes
        - Flags potential edge cases

        Returns:
            AgentResponse from LLM agent 1
        """
        self.log("Running LLM agent #1 (conservative)...")

        issues = self.feedback_data.get('issues', [])

        recommendations = []
        priority_items = []
        notes = ["LLM Agent 1: Conservative safety-focused analysis"]

        # Conservative analysis: focus on risks
        if len(issues) == 0:
            recommendations.append("Maintain current stable state")
            recommendations.append("Consider additional monitoring")
            priority_items.append({
                "type": "maintain_status_quo",
                "priority": 3
            })
        else:
            # Conservative: treat all issues seriously
            recommendations.append("Conduct thorough review of all reported issues")
            recommendations.append("Implement fixes incrementally with testing")
            recommendations.append("Increase monitoring during remediation")

            priority_items.append({
                "type": "comprehensive_review",
                "priority": 1
            })
            priority_items.append({
                "type": "incremental_remediation",
                "priority": 2
            })

        # Conservative agents have moderate confidence in complex situations
        confidence = 0.75 if len(issues) < 5 else 0.65

        # Conservative severity assessment: err on higher side
        severity = SeverityLevel.MEDIUM.value
        if any(i.get('severity') == 'critical' for i in issues):
            severity = SeverityLevel.CRITICAL.value
        elif any(i.get('severity') == 'high' for i in issues):
            severity = SeverityLevel.HIGH.value

        return AgentResponse(
            agent_name="llm_agent_1_conservative",
            recommendations=recommendations,
            priority_items=priority_items,
            confidence=confidence,
            severity_assessment=severity,
            notes=notes
        )

    def run_llm_agent_2(self) -> AgentResponse:
        """
        Mocked LLM Agent #2: Optimistic, efficiency-focused reasoning.

        This agent simulates an LLM with optimistic bias:
        - Prioritizes efficiency and progress
        - Suggests batch fixes
        - Focuses on quick wins

        Returns:
            AgentResponse from LLM agent 2
        """
        self.log("Running LLM agent #2 (optimistic)...")

        issues = self.feedback_data.get('issues', [])
        metrics = self.feedback_data.get('metrics', {})

        recommendations = []
        priority_items = []
        notes = ["LLM Agent 2: Optimistic efficiency-focused analysis"]

        if len(issues) == 0:
            recommendations.append("System performing well - consider optimization")
            recommendations.append("Explore enhancement opportunities")
            priority_items.append({
                "type": "optimization_opportunities",
                "priority": 4
            })
        else:
            # Optimistic: look for patterns and batch solutions
            recommendations.append("Group similar issues for batch resolution")
            recommendations.append("Prioritize high-impact quick wins")

            # Count fixable issues
            fixable = [i for i in issues if i.get('fixable', True)]
            if fixable:
                recommendations.append(f"Address {len(fixable)} fixable issues in parallel")
                priority_items.append({
                    "type": "batch_fixes",
                    "count": len(fixable),
                    "priority": 2
                })

        # Optimistic agents have higher confidence
        confidence = 0.85

        # Optimistic severity assessment: err on lower side
        severity = SeverityLevel.LOW.value
        if any(i.get('severity') == 'critical' for i in issues):
            severity = SeverityLevel.HIGH.value  # Still elevated, but not critical
        elif any(i.get('severity') == 'high' for i in issues):
            severity = SeverityLevel.MEDIUM.value

        return AgentResponse(
            agent_name="llm_agent_2_optimistic",
            recommendations=recommendations,
            priority_items=priority_items,
            confidence=confidence,
            severity_assessment=severity,
            notes=notes
        )

    def run_heuristics(self) -> AgentResponse:
        """
        Heuristics agent: statistical analysis and pattern detection.

        This agent analyzes:
        - Trend detection
        - Anomaly detection
        - Statistical thresholds
        - Historical patterns

        Returns:
            AgentResponse from heuristics agent
        """
        self.log("Running heuristics agent...")

        issues = self.feedback_data.get('issues', [])
        metrics = self.feedback_data.get('metrics', {})

        recommendations = []
        priority_items = []
        notes = ["Heuristics Agent: Statistical analysis"]

        # Heuristic 1: Issue rate analysis
        total_issues = len(issues)
        if total_issues == 0:
            recommendations.append("No anomalies detected")
            notes.append("Issue rate: 0 (baseline)")
        elif total_issues > 10:
            recommendations.append(f"High issue rate detected: {total_issues} issues")
            priority_items.append({
                "type": "high_issue_rate",
                "count": total_issues,
                "priority": 1
            })
            notes.append(f"Issue rate above threshold: {total_issues} > 10")
        else:
            notes.append(f"Issue rate normal: {total_issues}")

        # Heuristic 2: Metrics analysis
        if metrics:
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    if key.endswith('_rate') and value > 0.05:
                        recommendations.append(f"Elevated {key}: {value:.2%}")
                        priority_items.append({
                            "type": f"elevated_{key}",
                            "value": value,
                            "priority": 2
                        })

        # Heuristic 3: Pattern detection (simple clustering)
        issue_types = {}
        for issue in issues:
            itype = issue.get('type', 'unknown')
            issue_types[itype] = issue_types.get(itype, 0) + 1

        # Flag clustered issues
        for itype, count in issue_types.items():
            if count >= 3:
                recommendations.append(f"Pattern detected: {count} '{itype}' issues")
                priority_items.append({
                    "type": "clustered_issues",
                    "category": itype,
                    "count": count,
                    "priority": 2
                })
                notes.append(f"Cluster: {itype} x{count}")

        # Confidence based on data volume
        confidence = min(0.95, 0.5 + (total_issues * 0.05))

        # Severity based on statistical thresholds
        if total_issues == 0:
            severity = SeverityLevel.INFO.value
        elif total_issues > 10:
            severity = SeverityLevel.HIGH.value
        elif total_issues > 5:
            severity = SeverityLevel.MEDIUM.value
        else:
            severity = SeverityLevel.LOW.value

        return AgentResponse(
            agent_name="heuristics",
            recommendations=recommendations,
            priority_items=priority_items,
            confidence=confidence,
            severity_assessment=severity,
            notes=notes
        )

    def compute_consensus(self) -> Dict[str, Any]:
        """
        Compute consensus from all agent responses.

        Consensus algorithm:
        1. Agreement Score: How aligned are agent recommendations?
        2. Confidence: Weighted average of agent confidences
        3. Priority Items: Merged and ranked priorities
        4. Contradictions: Detect conflicting recommendations
        5. Final Recommendations: Consensus-weighted suggestions

        Returns:
            Consensus dictionary
        """
        self.log("Computing consensus across all agents...")

        if not self.agent_responses:
            return {
                "agreement_score": 0.0,
                "confidence": ConfidenceLevel.LOW.value,
                "priority_items": [],
                "contradictions": [],
                "final_recommendations": ["No agent responses available"],
                "stability_score": 0.0
            }

        # 1. Compute agreement score
        agreement_score = self._compute_agreement_score()

        # 2. Compute weighted confidence
        avg_confidence = sum(r.confidence for r in self.agent_responses) / len(self.agent_responses)
        confidence_bucket = self._confidence_to_bucket(avg_confidence)

        # 3. Merge and rank priority items
        merged_priorities = self._merge_priorities()

        # 4. Detect contradictions
        contradictions = self._detect_contradictions()

        # 5. Generate final recommendations
        final_recommendations = self._generate_final_recommendations(
            agreement_score,
            avg_confidence
        )

        # 6. Compute stability score (low = noisy/conflicting, high = stable/consistent)
        stability_score = self._compute_stability_score()

        self.log(f"Consensus computed: agreement={agreement_score:.2f}, "
                f"confidence={confidence_bucket}, stability={stability_score:.2f}")

        return {
            "agreement_score": round(agreement_score, 3),
            "confidence": confidence_bucket,
            "average_confidence": round(avg_confidence, 3),
            "priority_items": merged_priorities,
            "contradictions": contradictions,
            "final_recommendations": final_recommendations,
            "stability_score": round(stability_score, 3),
            "agent_count": len(self.agent_responses)
        }

    def _compute_agreement_score(self) -> float:
        """
        Compute agreement score between agents (0.0 to 1.0).

        Algorithm:
        - Compare severity assessments
        - Compare priority rankings
        - Compare recommendation overlap

        Returns:
            Agreement score 0.0 (total disagreement) to 1.0 (perfect agreement)
        """
        if len(self.agent_responses) < 2:
            return 1.0  # Single agent = perfect "agreement"

        # Severity agreement
        severities = [r.severity_assessment for r in self.agent_responses]
        severity_agreement = len(set(severities)) == 1

        # Confidence variance (low variance = higher agreement)
        confidences = [r.confidence for r in self.agent_responses]
        conf_variance = sum((c - sum(confidences)/len(confidences))**2 for c in confidences) / len(confidences)
        conf_agreement = 1.0 - min(conf_variance * 2, 1.0)  # Scale variance to 0-1

        # Recommendation overlap
        all_recs = [set(r.recommendations) for r in self.agent_responses]
        if all_recs:
            intersection = set.intersection(*all_recs) if len(all_recs) > 1 else all_recs[0]
            union = set.union(*all_recs) if all_recs else set()
            rec_agreement = len(intersection) / len(union) if union else 0.0
        else:
            rec_agreement = 1.0

        # Weighted average
        agreement = (
            (0.4 * (1.0 if severity_agreement else 0.5)) +
            (0.3 * conf_agreement) +
            (0.3 * rec_agreement)
        )

        return max(0.0, min(1.0, agreement))

    def _confidence_to_bucket(self, confidence: float) -> str:
        """Convert numeric confidence to bucket"""
        if confidence >= 0.8:
            return ConfidenceLevel.HIGH.value
        elif confidence >= 0.6:
            return ConfidenceLevel.MEDIUM.value
        else:
            return ConfidenceLevel.LOW.value

    def _merge_priorities(self) -> List[Dict[str, Any]]:
        """
        Merge priority items from all agents and rank them.

        Returns:
            Sorted list of priority items
        """
        all_priorities = []

        for response in self.agent_responses:
            for item in response.priority_items:
                # Add agent source
                item_copy = item.copy()
                item_copy['source_agent'] = response.agent_name
                item_copy['agent_confidence'] = response.confidence
                all_priorities.append(item_copy)

        # Sort by priority (lower number = higher priority)
        all_priorities.sort(key=lambda x: (x.get('priority', 999), -x.get('agent_confidence', 0)))

        # Take top 10
        return all_priorities[:10]

    def _detect_contradictions(self) -> List[Dict[str, Any]]:
        """
        Detect contradictions between agent recommendations.

        Returns:
            List of detected contradictions
        """
        contradictions = []

        # Check severity contradictions
        severities = [(r.agent_name, r.severity_assessment) for r in self.agent_responses]
        severity_set = set(s[1] for s in severities)

        if len(severity_set) > 2:  # More than 2 different severity levels
            contradictions.append({
                "type": "severity_disagreement",
                "details": dict(severities),
                "description": "Agents disagree on severity assessment"
            })

        # Check recommendation contradictions (simple keyword-based)
        conservative_keywords = {'maintain', 'incremental', 'thorough', 'review'}
        aggressive_keywords = {'batch', 'parallel', 'quick', 'optimization'}

        agent_styles = []
        for response in self.agent_responses:
            recs_text = ' '.join(response.recommendations).lower()
            conservative_score = sum(1 for kw in conservative_keywords if kw in recs_text)
            aggressive_score = sum(1 for kw in aggressive_keywords if kw in recs_text)

            if conservative_score > aggressive_score:
                agent_styles.append((response.agent_name, 'conservative'))
            elif aggressive_score > conservative_score:
                agent_styles.append((response.agent_name, 'aggressive'))

        # If we have both conservative and aggressive agents
        styles = [s[1] for s in agent_styles]
        if 'conservative' in styles and 'aggressive' in styles:
            contradictions.append({
                "type": "approach_disagreement",
                "details": dict(agent_styles),
                "description": "Agents disagree on remediation approach"
            })

        return contradictions

    def _compute_stability_score(self) -> float:
        """
        Compute stability score (inverse of noisiness/conflict).

        Returns:
            Stability score 0.0 (very unstable) to 1.0 (very stable)
        """
        if len(self.agent_responses) < 2:
            return 1.0

        # Confidence variance
        confidences = [r.confidence for r in self.agent_responses]
        conf_variance = sum((c - sum(confidences)/len(confidences))**2 for c in confidences) / len(confidences)

        # Recommendation count variance
        rec_counts = [len(r.recommendations) for r in self.agent_responses]
        rec_variance = sum((c - sum(rec_counts)/len(rec_counts))**2 for c in rec_counts) / len(rec_counts)
        rec_variance_normalized = min(rec_variance / 10.0, 1.0)  # Normalize

        # Stability is inverse of variance
        stability = 1.0 - ((conf_variance + rec_variance_normalized) / 2.0)

        return max(0.0, min(1.0, stability))

    def _generate_final_recommendations(self, agreement_score: float, avg_confidence: float) -> List[str]:
        """
        Generate final consensus recommendations.

        Args:
            agreement_score: Computed agreement score
            avg_confidence: Average confidence across agents

        Returns:
            List of final recommendations
        """
        recommendations = []

        # Collect all unique recommendations
        all_recs = []
        for response in self.agent_responses:
            all_recs.extend(response.recommendations)

        # Count frequency
        rec_frequency = {}
        for rec in all_recs:
            rec_frequency[rec] = rec_frequency.get(rec, 0) + 1

        # Sort by frequency (most common first)
        sorted_recs = sorted(rec_frequency.items(), key=lambda x: -x[1])

        # Add meta-recommendation based on consensus quality
        if agreement_score >= 0.8:
            recommendations.append(f"Strong consensus achieved (agreement: {agreement_score:.0%})")
        elif agreement_score >= 0.6:
            recommendations.append(f"Moderate consensus (agreement: {agreement_score:.0%}) - review conflicting points")
        else:
            recommendations.append(f"Low consensus (agreement: {agreement_score:.0%}) - manual review required")

        # Add top recommendations by frequency
        for rec, freq in sorted_recs[:5]:
            if freq > 1:
                recommendations.append(f"{rec} (supported by {freq}/{len(self.agent_responses)} agents)")
            else:
                recommendations.append(rec)

        return recommendations

    def generate_output(self) -> ConsensusOutput:
        """
        Generate the complete consensus output structure.

        Returns:
            ConsensusOutput object ready for JSON serialization
        """
        self.log("Generating consensus output...")

        # Run all agents
        self.agent_responses = [
            self.run_rules_engine(),
            self.run_llm_agent_1(),
            self.run_llm_agent_2(),
            self.run_heuristics()
        ]

        # Compute consensus
        consensus = self.compute_consensus()

        # Build agents section
        agents_output = {}
        for response in self.agent_responses:
            agents_output[response.agent_name] = {
                "recommendations": response.recommendations,
                "priority_items": response.priority_items,
                "confidence": round(response.confidence, 3),
                "severity_assessment": response.severity_assessment,
                "notes": response.notes
            }

        # Extract issues from feedback
        issues_detected = self.feedback_data.get('issues', []) if self.feedback_data else []

        # Collect all notes
        all_notes = self.notes.copy()
        for response in self.agent_responses:
            all_notes.extend(response.notes)

        output = ConsensusOutput(
            generated_at=datetime.utcnow().isoformat() + "Z",
            source=self.feedback_path,
            agents=agents_output,
            consensus=consensus,
            issues_detected=issues_detected,
            notes=all_notes,
            errors=self.errors
        )

        return output

    def save_output(self, output: ConsensusOutput) -> bool:
        """
        Save consensus output to JSON file.

        Args:
            output: ConsensusOutput object to save

        Returns:
            True if saved successfully, False otherwise
        """
        self.log(f"Saving consensus output to: {self.output_path}")

        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(self.output_path) if os.path.dirname(self.output_path) else '.', exist_ok=True)

            # Convert to dict and save
            output_dict = asdict(output)

            with open(self.output_path, 'w') as f:
                json.dump(output_dict, f, indent=2)

            self.log(f"Successfully saved consensus output ({os.path.getsize(self.output_path)} bytes)")
            return True

        except Exception as e:
            error_msg = f"Error saving output: {e}"
            self.errors.append(error_msg)
            self.log(f"ERROR: {error_msg}")
            return False

    def run(self) -> bool:
        """
        Execute the complete consensus engine pipeline.

        Pipeline:
        1. Load feedback
        2. Run all agents
        3. Compute consensus
        4. Generate output
        5. Save output

        Returns:
            True if successful, False if errors occurred
        """
        self.log("=" * 60)
        self.log("Hands-Off Engine - Consensus Feedback Engine v1")
        self.log("Batch 22: Multi-Agent Consensus Layer")
        self.log("=" * 60)

        # Load feedback
        load_success = self.load_feedback()

        # Generate consensus output
        output = self.generate_output()

        # Save output
        save_success = self.save_output(output)

        # Print summary
        if self.verbose:
            self._print_summary(output)

        success = save_success and len(self.errors) == 0

        self.log("=" * 60)
        self.log(f"Consensus engine completed: {'SUCCESS' if success else 'WITH ERRORS'}")
        self.log("=" * 60)

        return success

    def _print_summary(self, output: ConsensusOutput) -> None:
        """Print human-readable summary"""
        print("\n" + "=" * 60)
        print("CONSENSUS SUMMARY")
        print("=" * 60)

        print(f"\nSource: {output.source}")
        print(f"Generated: {output.generated_at}")
        print(f"Agents: {len(output.agents)}")

        consensus = output.consensus
        print(f"\nAgreement Score: {consensus['agreement_score']:.1%}")
        print(f"Confidence: {consensus['confidence'].upper()}")
        print(f"Stability Score: {consensus['stability_score']:.1%}")

        print(f"\nIssues Detected: {len(output.issues_detected)}")
        print(f"Priority Items: {len(consensus['priority_items'])}")
        print(f"Contradictions: {len(consensus['contradictions'])}")

        print("\nFinal Recommendations:")
        for i, rec in enumerate(consensus['final_recommendations'][:5], 1):
            print(f"  {i}. {rec}")

        if output.errors:
            print(f"\nERRORS ({len(output.errors)}):")
            for error in output.errors:
                print(f"  - {error}")

        print("\n" + "=" * 60)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Hands-Off Engine - Consensus Feedback Engine (Batch 22)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 ai/ho_consensus_engine.py --verbose
  python3 ai/ho_consensus_engine.py --input state/brain_feedback.json
  python3 ai/ho_consensus_engine.py --output state/custom_consensus.json
        """
    )

    parser.add_argument(
        '--input',
        default='state/brain_feedback.json',
        help='Path to input brain_feedback.json (default: state/brain_feedback.json)'
    )

    parser.add_argument(
        '--output',
        default='state/brain_consensus.json',
        help='Path to output brain_consensus.json (default: state/brain_consensus.json)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    # Create and run engine
    engine = ConsensusEngine(
        feedback_path=args.input,
        output_path=args.output,
        verbose=args.verbose
    )

    success = engine.run()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
