"""
Decider: The "Brain" of the Hands-Off Engine

This module converts alpha signals into structured planned actions.
It produces PlannedAction objects that represent trading intentions,
which are then validated and executed by the Executor (body).
"""

import json
import sys
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List
from datetime import datetime, timezone

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from audit import get_audit_logger

try:
    from ai_nexus.history_log import log_kernel_history_event
except ImportError:
    # History log may not be available in all configurations
    log_kernel_history_event = None


@dataclass
class PlannedAction:
    """Structured representation of a planned trading action"""
    market_id: str
    market_name: str
    side: str  # "YES" or "NO"
    amount: float  # Dollar amount to risk
    confidence: float  # 0.0 to 1.0
    reasoning: str  # Why this action makes sense


class Decider:
    """
    The Decider is the brain of the pipeline.
    It takes alpha signals and produces planned actions.
    """

    def __init__(self, bankroll: float = 1000.0, filter_expired: bool = True, apply_time_decay: bool = True):
        """
        Initialize the Decider.

        Args:
            bankroll: Total bankroll for position sizing (default: $1000)
            filter_expired: If True, filter out expired markets (default: True)
            apply_time_decay: If True, adjust position size for time decay (default: True)
        """
        self.bankroll = bankroll
        self.filter_expired = filter_expired
        self.apply_time_decay = apply_time_decay
        self.audit = get_audit_logger(component="decider")

    def decide(self):
        """Legacy method - kept for backwards compatibility"""
        print("Making a decision...")
        
        # Audit the decision
        self.audit.log_decision(
            decision_type="pipeline_decision",
            inputs={},
            outputs={"decision": "pending"}
        )

    def is_market_expired(self, market_name: str) -> bool:
        """
        Check if a market has expired based on its question text.

        Args:
            market_name: The market question text

        Returns:
            True if market appears to be expired, False otherwise
        """
        # Try to extract date from common patterns
        # Pattern 1: "on November 16", "in November", "by December 1"
        month_patterns = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }

        now = datetime.now(timezone.utc)
        market_lower = market_name.lower()

        # Check for specific dates like "November 16" or "Nov 16"
        for month_name, month_num in month_patterns.items():
            # Pattern: "month day" or "month day, year"
            pattern = rf'\b{month_name[:3]}(?:ember)?\s+(\d+)(?:,?\s+(\d{{4}}))?'
            match = re.search(pattern, market_lower)
            if match:
                day = int(match.group(1))
                year = int(match.group(2)) if match.group(2) else now.year

                # Construct the date
                try:
                    market_date = datetime(year, month_num, day, tzinfo=timezone.utc)
                    # Market is expired if date is in the past
                    if market_date < now:
                        return True
                except ValueError:
                    # Invalid date, skip
                    pass

        # Check for month-only expiration (e.g., "in November")
        for month_name, month_num in month_patterns.items():
            if f"in {month_name}" in market_lower or f"during {month_name}" in market_lower:
                # Month is past if we're in a later month
                if now.month > month_num:
                    return True
                # Or if same month but near end (after 25th), mark as risky
                # We'll just let this through and handle with time decay

        return False

    def get_days_to_expiration(self, market_name: str) -> float:
        """
        Estimate days until market expiration.

        Args:
            market_name: The market question text

        Returns:
            Estimated days to expiration (returns 30.0 if can't determine)
        """
        month_patterns = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }

        now = datetime.now(timezone.utc)
        market_lower = market_name.lower()

        # Check for specific dates
        for month_name, month_num in month_patterns.items():
            pattern = rf'\b{month_name[:3]}(?:ember)?\s+(\d+)(?:,?\s+(\d{{4}}))?'
            match = re.search(pattern, market_lower)
            if match:
                day = int(match.group(1))
                year = int(match.group(2)) if match.group(2) else now.year

                try:
                    market_date = datetime(year, month_num, day, tzinfo=timezone.utc)
                    days_remaining = (market_date - now).total_seconds() / 86400
                    return max(0, days_remaining)
                except ValueError:
                    pass

        # If month only, assume end of month
        for month_name, month_num in month_patterns.items():
            if f"in {month_name}" in market_lower:
                # Use last day of month
                if month_num in [1, 3, 5, 7, 8, 10, 12]:
                    last_day = 31
                elif month_num in [4, 6, 9, 11]:
                    last_day = 30
                else:
                    last_day = 28  # February (simplified)

                year = now.year
                if month_num < now.month:
                    year += 1

                try:
                    market_date = datetime(year, month_num, last_day, tzinfo=timezone.utc)
                    days_remaining = (market_date - now).total_seconds() / 86400
                    return max(0, days_remaining)
                except ValueError:
                    pass

        # Default: assume 30 days if we can't determine
        return 30.0

    def load_model_signals(self, model_path: Path) -> List[dict]:
        """
        Load alpha signals from polymarket-model.json file.

        Args:
            model_path: Path to polymarket-model.json

        Returns:
            List of alpha signal dicts in the format expected by plan_actions
        """
        with open(model_path, 'r') as f:
            model_data = json.load(f)

        # Transform model format to internal alpha signals format
        alpha_signals = []
        for market in model_data.get('markets', []):
            # Check if market is expired (if filtering enabled)
            if self.filter_expired and self.is_market_expired(market['question']):
                print(f"[decider] Filtering expired market: {market['question']}")
                continue

            signal = {
                'market_id': market['market_id'],
                'market_name': market['question'],
                'edge': market['model_edge'],
                'current_odds': market['market_price'],
                'side': market['side'],
                'model_confidence': market['model_confidence'],
                'fair_price': market['fair_price']
            }
            alpha_signals.append(signal)

        return alpha_signals

    def plan_actions(self, alpha_signals: List[dict]) -> List[PlannedAction]:
        """
        Convert alpha signals into planned actions.

        Args:
            alpha_signals: List of dicts with keys:
                - market_id: str
                - market_name: str
                - edge: float (expected edge, e.g., 0.05 for 5%)
                - current_odds: float (current market odds)
                - side: str ("YES" or "NO")
                - model_confidence: float (optional, from model)

        Returns:
            List of PlannedAction objects representing trading intentions
        """
        planned_actions = []

        for signal in alpha_signals:
            # Get edge and model confidence
            edge = signal.get('edge', 0.0)
            model_confidence = signal.get('model_confidence')
            
            # Use model confidence if available, otherwise derive from edge
            if model_confidence is not None:
                confidence = model_confidence
            else:
                confidence = 0.5 + (edge * 5)  # Simple scaling: 5% edge -> 0.75 confidence
                confidence = max(0.0, min(1.0, confidence))  # Clamp to [0, 1]

            # Size position based on edge and confidence
            # Kelly criterion approximation: f = (edge * confidence) / odds
            # Simplified: use a fraction of bankroll proportional to edge * confidence
            kelly_fraction = edge * confidence
            max_fraction = 0.10  # Never risk more than 10% of bankroll per position
            size_fraction = min(kelly_fraction, max_fraction)
            amount = self.bankroll * size_fraction

            # Apply time decay adjustment if enabled
            time_decay_factor = 1.0
            days_to_expiration = None
            if self.apply_time_decay:
                days_to_expiration = self.get_days_to_expiration(signal['market_name'])
                if days_to_expiration < 1:
                    time_decay_factor = 0.0  # Don't trade day-of expiration
                elif days_to_expiration < 3:
                    time_decay_factor = 0.5  # Half size for <3 days
                elif days_to_expiration < 7:
                    time_decay_factor = 0.75  # 75% size for <7 days
                amount *= time_decay_factor

            # Create reasoning string
            reasoning_parts = [
                f"Edge: {edge:.1%}",
                f"Odds: {signal.get('current_odds', 0):.2f}",
                f"Confidence: {confidence:.1%}"
            ]
            if self.apply_time_decay and days_to_expiration is not None:
                reasoning_parts.append(f"Days to exp: {days_to_expiration:.1f}")
                if time_decay_factor < 1.0:
                    reasoning_parts.append(f"Time decay: {time_decay_factor:.0%}")
            reasoning = ", ".join(reasoning_parts)

            action = PlannedAction(
                market_id=signal['market_id'],
                market_name=signal['market_name'],
                side=signal['side'],
                amount=amount,
                confidence=confidence,
                reasoning=reasoning
            )

            planned_actions.append(action)

            # Log risk decision for Spark Plug kernels (if available)
            if log_kernel_history_event:
                try:
                    log_kernel_history_event(
                        kernel_ids=["risk_model_v2", "trading_philosophy"],
                        kind="risk_decision",
                        source="risk_model_v2",
                        summary=f"Risk decision for {signal['market_id']}: f={kelly_fraction:.3f}, size=${amount:.2f}, edge={edge:.3f}, conf={confidence:.2f}",
                        details={
                            "market_id": signal['market_id'],
                            "market_name": signal['market_name'],
                            "side": signal['side'],
                            "edge": edge,
                            "confidence": confidence,
                            "kelly_raw": kelly_fraction,
                            "kelly_used": size_fraction,
                            "size_usd": amount,
                            "current_odds": signal.get('current_odds', None),
                            "fair_price": signal.get('fair_price', None),
                        },
                        importance=8,
                        tags=["risk_v2", "kelly"],
                    )
                except Exception as e:
                    # Best-effort logging - never crash the decider
                    print(f"[history_log] Warning: Failed to log risk decision: {e}")

        # Log aggregate decider outcome for Spark Plug kernels (if available)
        if log_kernel_history_event:
            try:
                total_risk_usd = sum(action.amount for action in planned_actions)
                num_buys = sum(1 for action in planned_actions if action.side == "YES")
                num_sells = sum(1 for action in planned_actions if action.side == "NO")

                log_kernel_history_event(
                    kernel_ids=["risk_model_v2", "alpha_polymarket_core", "trading_philosophy"],
                    kind="decider_outcome",
                    source="ho_decider",
                    summary=f"Decider produced {len(planned_actions)} decisions, total_risk=${total_risk_usd:.2f}, buys={num_buys}, sells={num_sells}",
                    details={
                        "num_decisions": len(planned_actions),
                        "total_risk_usd": total_risk_usd,
                        "num_buys": num_buys,
                        "num_sells": num_sells,
                        "market_ids": [action.market_id for action in planned_actions],
                        "bankroll": self.bankroll,
                    },
                    importance=7,
                    tags=["decider", "aggregate"],
                )
            except Exception as e:
                # Best-effort logging - never crash the decider
                print(f"[history_log] Warning: Failed to log decider outcome: {e}")

        return planned_actions


# Instantiate and decide (for backwards compatibility)
if __name__ == "__main__":
    decider = Decider()
    decider.decide()
