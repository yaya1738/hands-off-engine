#!/usr/bin/env python3
"""
INTEGRAFIX: Trading Memory
===========================

PROBLEM SOLVED:
AI has no memory of past trading decisions.
Each session starts fresh with no context.

SOLUTION:
1. Remember successful trading patterns
2. Store market insights that worked
3. Track which strategies performed well
4. Feed this context to trading decisions

This connects AI memory to trading for continuous learning.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"


class TradingMemory:
    """
    Connects AI memory to trading decisions.
    Remembers what worked and what didn't.
    """

    def __init__(self):
        from integrafix.ai_memory import get_memory, MemoryType, MemoryPriority

        self.memory = get_memory()
        self.MemoryType = MemoryType
        self.MemoryPriority = MemoryPriority

    def remember_trade_outcome(
        self,
        market_question: str,
        side: str,
        outcome: str,  # WIN/LOSS
        pnl: float,
        reasoning: str,
        edge: float,
    ):
        """Remember a trade outcome for future reference."""
        content = f"{outcome}: {side} on '{market_question[:50]}' | P&L: ${pnl:+.2f} | Edge: {edge:.1%}"

        priority = self.MemoryPriority.HIGH if pnl > 10 else self.MemoryPriority.MEDIUM

        # Use LEARNING for wins, ERROR for losses
        memory_type = self.MemoryType.SUCCESS if outcome == "WIN" else self.MemoryType.LEARNING

        self.memory.remember(
            content=content,
            memory_type=memory_type,
            priority=priority,
            context=f"Trade {outcome.lower()}: {reasoning}",
            tags=["trading", outcome.lower(), side.lower()],
        )

    def remember_market_insight(
        self,
        insight: str,
        category: str,
        confidence: float,
    ):
        """Remember a market insight."""
        content = f"[{category.upper()}] {insight}"

        self.memory.remember(
            content=content,
            memory_type=self.MemoryType.INSIGHT,
            priority=self.MemoryPriority.MEDIUM,
            context=f"Market insight (confidence: {confidence:.0%})",
            tags=["market", category],
        )

    def remember_strategy_performance(
        self,
        strategy: str,
        win_rate: float,
        total_pnl: float,
        trade_count: int,
    ):
        """Remember how a strategy performed."""
        content = f"Strategy '{strategy}': {win_rate:.0%} win rate, ${total_pnl:+.2f} P&L over {trade_count} trades"

        priority = self.MemoryPriority.CRITICAL if win_rate > 0.6 else self.MemoryPriority.LOW

        self.memory.remember(
            content=content,
            memory_type=self.MemoryType.DECISION,
            priority=priority,
            context="Strategy performance tracking",
            tags=["strategy", strategy],
        )

    def get_trading_context(self, market_category: Optional[str] = None) -> Dict:
        """
        Get relevant trading context from memory.
        This informs new trading decisions.
        """
        context = {
            "recent_wins": [],
            "recent_losses": [],
            "insights": [],
            "strategy_notes": [],
            "total_memories": 0,
        }

        # Get trading-related memories using recall_about
        trading_memories = self.memory.recall_about("trading")
        context["total_memories"] = len(trading_memories)

        for m in trading_memories[:20]:  # Recent 20
            tags = getattr(m, 'tags', []) or []
            content = getattr(m, 'content', str(m))
            if "win" in tags or "WIN" in content:
                context["recent_wins"].append(content)
            elif "loss" in tags or "LOSS" in content:
                context["recent_losses"].append(content)

        # Get market insights
        insight_memories = self.memory.recall_about("market")
        if market_category:
            insight_memories = [m for m in insight_memories
                              if market_category in str(getattr(m, 'tags', []))]

        for m in insight_memories[:10]:
            context["insights"].append(getattr(m, 'content', str(m)))

        # Get strategy notes
        strategy_memories = self.memory.recall_about("strategy")
        for m in strategy_memories[:5]:
            context["strategy_notes"].append(getattr(m, 'content', str(m)))

        return context

    def generate_trading_wisdom(self) -> List[str]:
        """
        Generate trading wisdom from accumulated memories.
        This can be used to improve edge detection.
        """
        wisdom = []

        context = self.get_trading_context()

        win_count = len(context["recent_wins"])
        loss_count = len(context["recent_losses"])
        total = win_count + loss_count

        if total >= 5:
            win_rate = win_count / total
            if win_rate > 0.6:
                wisdom.append(f"Current strategy is working well ({win_rate:.0%} win rate)")
            elif win_rate < 0.4:
                wisdom.append(f"Current strategy needs adjustment ({win_rate:.0%} win rate)")

        # Extract patterns from wins
        yes_wins = sum(1 for w in context["recent_wins"] if "YES" in w)
        no_wins = sum(1 for w in context["recent_wins"] if "NO" in w)

        if yes_wins > no_wins * 2:
            wisdom.append("YES bets have been more successful recently")
        elif no_wins > yes_wins * 2:
            wisdom.append("NO bets have been more successful recently")

        return wisdom

    def sync_from_outcomes(self):
        """
        Sync memories from outcome tracker.
        Called after trades resolve.
        """
        from integrafix.outcome_tracker import get_tracker

        tracker = get_tracker()

        # Load recent outcomes
        outcomes_file = STATE_DIR / "trade_outcomes.jsonl"
        if not outcomes_file.exists():
            return

        recent_outcomes = []
        with open(outcomes_file) as f:
            for line in f:
                try:
                    outcome = json.loads(line)
                    recent_outcomes.append(outcome)
                except:
                    pass

        # Remember recent outcomes (last 10)
        for o in recent_outcomes[-10:]:
            self.remember_trade_outcome(
                market_question=o.get("market_id", "unknown"),
                side=o.get("side", ""),
                outcome="WIN" if o.get("was_correct") else "LOSS",
                pnl=o.get("pnl", 0),
                reasoning=f"Edge predicted: {o.get('edge_predicted', 0):.1%}",
                edge=o.get("edge_predicted", 0),
            )

    def status(self) -> Dict:
        """Get trading memory status."""
        context = self.get_trading_context()
        wisdom = self.generate_trading_wisdom()

        return {
            "total_trading_memories": context["total_memories"],
            "recent_wins": len(context["recent_wins"]),
            "recent_losses": len(context["recent_losses"]),
            "insights_count": len(context["insights"]),
            "wisdom": wisdom,
        }


# Singleton
_trading_memory = None

def get_trading_memory() -> TradingMemory:
    global _trading_memory
    if _trading_memory is None:
        _trading_memory = TradingMemory()
    return _trading_memory


def main():
    """Test trading memory."""
    tm = get_trading_memory()

    print("=" * 70)
    print("INTEGRAFIX: Trading Memory")
    print("=" * 70)

    # Sync from outcomes
    print("\nSyncing from outcome tracker...")
    tm.sync_from_outcomes()

    status = tm.status()
    print(f"\nTrading Memories: {status['total_trading_memories']}")
    print(f"Recent Wins: {status['recent_wins']}")
    print(f"Recent Losses: {status['recent_losses']}")
    print(f"Insights: {status['insights_count']}")

    print("\nTrading Wisdom:")
    for w in status["wisdom"]:
        print(f"  - {w}")

    # Show context
    print("\nTrading Context:")
    context = tm.get_trading_context()
    if context["recent_wins"]:
        print("  Recent Wins:")
        for win in context["recent_wins"][:3]:
            print(f"    {win}")
    if context["recent_losses"]:
        print("  Recent Losses:")
        for loss in context["recent_losses"][:3]:
            print(f"    {loss}")


if __name__ == "__main__":
    main()
