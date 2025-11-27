#!/usr/bin/env python3
"""
Fed Rate Analyzer: Alpha Signals for Federal Reserve Rate Decisions
====================================================================

This module analyzes Fed rate decision markets by:
1. Estimating fair probabilities from CME FedWatch-style data
2. Comparing to Polymarket odds
3. Identifying edge opportunities

The Fed funds futures market provides forward-looking probabilities
for rate decisions, which can be compared to prediction market odds.

Key concepts:
- Fed funds futures price → implied probability of rate level
- CME FedWatch methodology: probability distribution from futures prices
- Edge = our fair price - market price (when betting YES)
"""

import json
import sys
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger


@dataclass
class FedRateScenario:
    """Represents a possible Fed rate outcome"""
    target_rate_bps: int  # Target rate in basis points (e.g., 425 = 4.25%)
    description: str  # e.g., "25bps cut", "hold", "25bps hike"
    fair_probability: float  # Our estimated probability (0.0 to 1.0)
    market_probability: Optional[float] = None  # Polymarket odds if available


@dataclass
class FedMeetingAnalysis:
    """Analysis results for a Fed meeting"""
    meeting_date: str  # ISO date of FOMC meeting
    current_rate_bps: int  # Current Fed funds rate in bps
    scenarios: List[FedRateScenario]
    recommended_scenario: Optional[str] = None  # Which scenario has edge
    edge: float = 0.0  # Calculated edge
    confidence: float = 0.0  # Confidence in the analysis


class FedRateAnalyzer:
    """
    Analyzer for Federal Reserve rate decision markets.

    Uses CME FedWatch-style methodology to estimate fair probabilities
    and compares them to Polymarket odds.
    """

    # Current Fed Funds Target Rate (as of late 2024)
    # Target range: 4.50% - 4.75% (midpoint: 4.625%)
    CURRENT_TARGET_RATE_BPS = 450  # Lower bound of target range

    # Standard rate move increments
    RATE_MOVE_BPS = 25  # Standard 25 basis point move

    def __init__(self):
        """Initialize the Fed Rate Analyzer"""
        self.audit = get_audit_logger(component="alpha.fed_rate")

    def _calculate_implied_probability_from_futures(
        self,
        futures_price: float,
        current_rate_bps: int,
        meeting_rate_bps: int
    ) -> float:
        """
        Calculate implied probability of a rate outcome from futures price.

        The Fed funds futures price (100 - rate) implies the expected
        average Fed funds rate for that month. We can derive probabilities
        of different outcomes from this.

        Args:
            futures_price: Fed funds futures price (e.g., 95.5 implies 4.5% rate)
            current_rate_bps: Current Fed funds rate in basis points
            meeting_rate_bps: Rate outcome we're calculating probability for

        Returns:
            Implied probability (0.0 to 1.0)
        """
        # Implied rate from futures = 100 - futures_price
        implied_rate = (100 - futures_price) * 100  # Convert to bps

        # Simple linear interpolation between current rate and target rate
        # This is a simplified CME FedWatch methodology
        if abs(meeting_rate_bps - current_rate_bps) < 1:
            # Probability of "no change"
            prob = 1.0 - abs(implied_rate - current_rate_bps) / self.RATE_MOVE_BPS
        else:
            # Probability of rate move
            prob = abs(implied_rate - current_rate_bps) / self.RATE_MOVE_BPS

        return max(0.0, min(1.0, prob))

    def estimate_fair_probabilities(
        self,
        fed_futures_data: Optional[Dict] = None,
        meeting_date: str = "2025-12-17"  # December 2025 FOMC
    ) -> List[FedRateScenario]:
        """
        Estimate fair probabilities for Fed rate scenarios.

        Uses fed funds futures data when available, otherwise uses
        market consensus estimates.

        Args:
            fed_futures_data: Optional dict with futures prices
            meeting_date: ISO date string for the FOMC meeting

        Returns:
            List of FedRateScenario with fair probabilities
        """
        current_rate = self.CURRENT_TARGET_RATE_BPS

        # Define possible scenarios for December 2025 FOMC
        # Based on current market expectations (late 2024)
        scenarios = []

        if fed_futures_data:
            # Use actual futures data if available
            futures_price = fed_futures_data.get('price', 95.25)
            implied_rate = (100 - futures_price) * 100

            # Calculate probabilities based on futures
            prob_cut_50 = self._calculate_implied_probability_from_futures(
                futures_price, current_rate, current_rate - 50
            )
            prob_cut_25 = self._calculate_implied_probability_from_futures(
                futures_price, current_rate, current_rate - 25
            )
            prob_hold = 1.0 - prob_cut_50 - prob_cut_25

            # Normalize probabilities
            total = prob_cut_50 + prob_cut_25 + max(0, prob_hold)
            if total > 0:
                prob_cut_50 /= total
                prob_cut_25 /= total
                prob_hold = max(0, prob_hold) / total
        else:
            # Default to consensus estimates (these should be updated
            # with actual market data in production)
            prob_cut_25 = 0.65  # 25bps cut most likely
            prob_hold = 0.25   # Hold second most likely
            prob_cut_50 = 0.10  # 50bps cut less likely

        scenarios = [
            FedRateScenario(
                target_rate_bps=current_rate - 50,
                description="50bps cut",
                fair_probability=round(prob_cut_50, 4)
            ),
            FedRateScenario(
                target_rate_bps=current_rate - 25,
                description="25bps cut",
                fair_probability=round(prob_cut_25, 4)
            ),
            FedRateScenario(
                target_rate_bps=current_rate,
                description="hold",
                fair_probability=round(prob_hold, 4)
            ),
        ]

        return scenarios

    def fetch_polymarket_odds(
        self,
        polymarket_data: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Fetch current Polymarket odds for Fed rate outcomes.

        Args:
            polymarket_data: Optional dict with Polymarket market data

        Returns:
            Dict mapping outcome descriptions to market prices
        """
        if polymarket_data:
            # Extract odds from provided data
            return {
                "25bps cut": polymarket_data.get("25bps_cut", 0.5),
                "hold": polymarket_data.get("hold", 0.3),
                "50bps cut": polymarket_data.get("50bps_cut", 0.1),
            }
        else:
            # Default placeholder - in production, would fetch from Polymarket API
            return {
                "25bps cut": 0.55,
                "hold": 0.30,
                "50bps cut": 0.10,
            }

    def calculate_edge(
        self,
        fair_prob: float,
        market_prob: float
    ) -> Tuple[float, str]:
        """
        Calculate edge and determine which side to bet.

        Args:
            fair_prob: Our estimated fair probability
            market_prob: Market's implied probability

        Returns:
            Tuple of (edge amount, side to bet)
        """
        edge = fair_prob - market_prob

        if edge > 0:
            # Fair prob higher than market → bet YES (outcome is underpriced)
            return (edge, "YES")
        else:
            # Fair prob lower than market → bet NO (outcome is overpriced)
            return (abs(edge), "NO")

    def calculate_confidence(
        self,
        edge: float,
        liquidity: float = 1000000.0,
        time_to_meeting_days: int = 30
    ) -> float:
        """
        Calculate confidence in the edge estimate.

        Factors:
        - Higher edges are more suspicious (lower confidence)
        - Higher liquidity markets are more efficient (higher confidence)
        - Closer to meeting = more information available (higher confidence)

        Args:
            edge: The calculated edge
            liquidity: Market liquidity in USD
            time_to_meeting_days: Days until FOMC meeting

        Returns:
            Confidence score (0.0 to 1.0)
        """
        # Base confidence
        confidence = 0.7

        # Reduce confidence for very high edges (suspicious)
        if edge > 0.15:
            confidence *= 0.5
        elif edge > 0.10:
            confidence *= 0.7
        elif edge > 0.05:
            confidence *= 0.9

        # Adjust for liquidity (higher liquidity = more efficient market)
        if liquidity > 100_000_000:  # $100M+
            confidence *= 0.95  # High liquidity = trust market more
        elif liquidity > 10_000_000:  # $10M+
            confidence *= 0.98
        # Lower liquidity = more opportunity but also more noise

        # Adjust for time to meeting
        if time_to_meeting_days < 7:
            confidence *= 1.1  # More information close to meeting
        elif time_to_meeting_days > 60:
            confidence *= 0.8  # More uncertainty further out

        return max(0.0, min(1.0, confidence))

    def analyze_fed_meeting(
        self,
        meeting_date: str = "2025-12-17",
        fed_futures_data: Optional[Dict] = None,
        polymarket_data: Optional[Dict] = None,
        market_volume_usd: float = 159_000_000.0
    ) -> FedMeetingAnalysis:
        """
        Full analysis of a Fed meeting market.

        Args:
            meeting_date: ISO date of FOMC meeting
            fed_futures_data: Optional Fed futures price data
            polymarket_data: Optional Polymarket odds data
            market_volume_usd: Total market volume in USD

        Returns:
            FedMeetingAnalysis with recommendations
        """
        # Get fair probabilities
        scenarios = self.estimate_fair_probabilities(
            fed_futures_data=fed_futures_data,
            meeting_date=meeting_date
        )

        # Get market odds
        market_odds = self.fetch_polymarket_odds(polymarket_data)

        # Calculate edge for each scenario
        best_edge = 0.0
        best_scenario = None
        best_side = None

        for scenario in scenarios:
            market_prob = market_odds.get(scenario.description, 0.5)
            scenario.market_probability = market_prob

            edge, side = self.calculate_edge(scenario.fair_probability, market_prob)

            if edge > best_edge:
                best_edge = edge
                best_scenario = scenario
                best_side = side

        # Calculate confidence
        confidence = self.calculate_confidence(
            edge=best_edge,
            liquidity=market_volume_usd
        )

        analysis = FedMeetingAnalysis(
            meeting_date=meeting_date,
            current_rate_bps=self.CURRENT_TARGET_RATE_BPS,
            scenarios=scenarios,
            recommended_scenario=f"{best_scenario.description} ({best_side})" if best_scenario else None,
            edge=round(best_edge, 4),
            confidence=round(confidence, 4)
        )

        # Audit the analysis
        self.audit.log_action(
            action_type="fed_rate_analysis",
            action_data={
                "meeting_date": meeting_date,
                "scenarios": len(scenarios),
                "best_edge": best_edge,
                "confidence": confidence,
                "recommendation": analysis.recommended_scenario
            },
            result="completed"
        )

        return analysis

    def generate_alpha_signals(
        self,
        analysis: FedMeetingAnalysis,
        min_edge: float = 0.05
    ) -> List[Dict]:
        """
        Generate alpha signals from Fed meeting analysis.

        This produces signals in the format expected by the Decider.

        Args:
            analysis: FedMeetingAnalysis from analyze_fed_meeting
            min_edge: Minimum edge threshold to include

        Returns:
            List of alpha signal dicts
        """
        signals = []

        for scenario in analysis.scenarios:
            if scenario.market_probability is None:
                continue

            edge, side = self.calculate_edge(
                scenario.fair_probability,
                scenario.market_probability
            )

            if edge < min_edge:
                continue

            # Generate market_id in consistent format
            meeting_short = analysis.meeting_date.replace("-", "")
            rate_str = f"{scenario.target_rate_bps}bps"
            market_id = f"fed-rate-{meeting_short}-{scenario.description.replace(' ', '-')}"

            signal = {
                "market_id": market_id,
                "question": f"Will the Fed {scenario.description} at the {analysis.meeting_date} meeting?",
                "query_category": "fed_rate",
                "side": side,
                "model_edge": round(edge, 4),
                "model_confidence": analysis.confidence,
                "fair_price": scenario.fair_probability,
                "market_price": scenario.market_probability,
                "best_bid": scenario.market_probability * 0.95,  # Estimate
                "liquidity": 10000.0,  # Placeholder
                "metadata": {
                    "meeting_date": analysis.meeting_date,
                    "target_rate_bps": scenario.target_rate_bps,
                    "current_rate_bps": analysis.current_rate_bps,
                    "scenario_type": scenario.description
                }
            }

            signals.append(signal)

        return signals


def analyze_december_fomc(
    output_path: Optional[Path] = None,
    fed_futures_data: Optional[Dict] = None,
    polymarket_data: Optional[Dict] = None
) -> Dict:
    """
    Convenience function to analyze December 2025 FOMC meeting.

    Args:
        output_path: Optional path to write results
        fed_futures_data: Optional Fed futures data
        polymarket_data: Optional Polymarket data

    Returns:
        Analysis results dict
    """
    analyzer = FedRateAnalyzer()

    # Analyze the meeting
    analysis = analyzer.analyze_fed_meeting(
        meeting_date="2025-12-17",
        fed_futures_data=fed_futures_data,
        polymarket_data=polymarket_data,
        market_volume_usd=159_000_000.0  # From problem statement
    )

    # Generate alpha signals
    signals = analyzer.generate_alpha_signals(analysis)

    # Build output
    result = {
        "generated_at": datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        "analysis_type": "fed_rate",
        "meeting_date": analysis.meeting_date,
        "current_rate_bps": analysis.current_rate_bps,
        "recommendation": analysis.recommended_scenario,
        "edge": analysis.edge,
        "confidence": analysis.confidence,
        "scenarios": [asdict(s) for s in analysis.scenarios],
        "alpha_signals": signals
    }

    # Write to file if path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_tmp = output_path.with_suffix('.tmp')
        with open(output_tmp, 'w') as f:
            json.dump(result, f, indent=2)
        output_tmp.replace(output_path)

    return result


def main():
    """Main entry point for CLI usage"""
    repo_root = Path(__file__).parent.parent
    output_path = repo_root / 'state' / 'fed_rate_analysis.json'

    print("🏛️  Fed Rate Analyzer")
    print("=" * 50)
    print()

    try:
        result = analyze_december_fomc(output_path=output_path)

        print(f"Meeting: {result['meeting_date']}")
        print(f"Current Rate: {result['current_rate_bps']}bps ({result['current_rate_bps']/100:.2f}%)")
        print()

        print("Scenarios:")
        for scenario in result['scenarios']:
            fair = scenario['fair_probability']
            market = scenario.get('market_probability', 'N/A')
            market_str = f"{market:.1%}" if isinstance(market, float) else market
            print(f"  {scenario['description']}: Fair={fair:.1%}, Market={market_str}")
        print()

        if result['recommendation']:
            print(f"📊 Recommendation: {result['recommendation']}")
            print(f"   Edge: {result['edge']:.1%}")
            print(f"   Confidence: {result['confidence']:.1%}")
        else:
            print("No edge detected above threshold.")
        print()

        print(f"Alpha signals generated: {len(result['alpha_signals'])}")
        print(f"Output written to: {output_path}")

        return 0

    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
