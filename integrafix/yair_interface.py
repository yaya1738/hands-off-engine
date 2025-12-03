#!/usr/bin/env python3
"""
INTEGRAFIX: Yair Siegel Interface
=================================

Optimal human-machine interaction interface for Yair.

DESIGN PRINCIPLES:
==================
1. Minimal friction - One-liner commands
2. Async-friendly - Review when convenient
3. Clear value - Show what machine can't do alone
4. Feedback loop - Learn from outcomes

CAPABILITIES BY ENTITY:
=======================

MACHINE (24/7, instant):
- Scan markets for opportunities
- Calculate position sizes (Kelly)
- Execute trades
- Monitor positions
- Track outcomes
- Generate reports

HUMAN (Yair, async):
- Provide probability estimates (edge detection)
- Approve/veto large trades
- Set strategic direction
- Review calibration
- Risk tolerance updates

INTERFACE METHODS:
==================
1. CLI: Quick commands for terminal
2. JSON files: For programmatic access
3. Status page: Visual dashboard
4. Telegram: Push notifications (existing)

Serving: Yair Siegel
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
sys.path.insert(0, str(PROJECT_ROOT))


class YairInterface:
    """
    Unified interface for Yair to interact with the system.

    Designed for minimal friction and maximum value.
    """

    def __init__(self):
        self._load_components()

    def _load_components(self):
        """Lazy load components."""
        self._synergy = None
        self._orchestrator = None
        self._nexus = None

    @property
    def synergy(self):
        if self._synergy is None:
            from integrafix.human_machine_synergy import HumanMachineSynergy
            self._synergy = HumanMachineSynergy()
            self._synergy.min_edge_for_action = 0.03
        return self._synergy

    @property
    def orchestrator(self):
        if self._orchestrator is None:
            from integrafix.abcfc_orchestrator import ABCFCOrchestrator
            self._orchestrator = ABCFCOrchestrator(dry_run=True)
        return self._orchestrator

    @property
    def nexus(self):
        if self._nexus is None:
            from integrafix.abcfc_live_nexus import ABCFCLiveNexus
            self._nexus = ABCFCLiveNexus(dry_run=True)
            self._nexus.min_edge = 0.03
        return self._nexus

    # =========================================================================
    # QUICK COMMANDS (One-liners for Yair)
    # =========================================================================

    def status(self) -> str:
        """
        Quick status: What does Yair need to know right now?

        Usage: yair status
        """
        lines = [
            "=" * 60,
            "YAIR SIEGEL - QUICK STATUS",
            f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "=" * 60,
        ]

        # Get orchestrator state
        try:
            state = self.orchestrator.observe()
            lines.append(f"\n>>> ABCFC STATUS")
            lines.append(f"    Nodes: {state.hierarchy_nodes}")
            lines.append(f"    Expected: ${state.total_expected:+,.0f}")
            lines.append(f"    Risk-Adj: ${state.risk_adjusted_expected:+,.0f}")
        except Exception as e:
            lines.append(f"\n>>> ABCFC: Error - {e}")

        # Get live trading status
        try:
            self.nexus.observe()
            self.nexus.generate_actions()
            actions = self.nexus.decide(max_actions=5)
            lines.append(f"\n>>> LIVE TRADING")
            lines.append(f"    Markets: {len(self.nexus.market_data)}")
            lines.append(f"    Actions ready: {len(actions)}")
            if actions:
                lines.append(f"    Top action: {actions[0].market_slug[:30]}")
                lines.append(f"    E[P&L]: ${actions[0].expected_pnl:.2f}")
        except Exception as e:
            lines.append(f"\n>>> LIVE: Error - {e}")

        # Get pending human input
        pending = self.synergy.get_pending_for_human()
        total_pending = pending["summary"]["total_pending"]
        if total_pending > 0:
            lines.append(f"\n>>> NEEDS YOUR INPUT: {total_pending} items")
            lines.append(f"    Run: yair review")
        else:
            lines.append(f"\n>>> No items need your input")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    def review(self) -> str:
        """
        Show items needing human review with knowledge context.

        Usage: yair review
        """
        # Get knowledge context
        try:
            from integrafix.synergy_knowledge_bridge import SynergyKnowledgeBridge
            bridge = SynergyKnowledgeBridge()
            context = bridge.get_decision_context()

            lines = [
                self.synergy.render_input_interface(),
                "",
                ">>> KNOWLEDGE CONTEXT (from system success)",
                f"    Success patterns: {', '.join(context.success_patterns[:3]) if context.success_patterns else 'None yet'}",
                f"    Recommendations:",
            ]
            for rec in context.recommended_actions[:3]:
                lines.append(f"      • {rec}")

            return "\n".join(lines)
        except:
            return self.synergy.render_input_interface()

    def estimate(self, market_id: str, probability: float, notes: str = "") -> str:
        """
        Submit probability estimate for a market.

        Usage: yair estimate MARKET_ID 0.65 "Reason"
        """
        if not 0 <= probability <= 1:
            return "Error: Probability must be between 0 and 1"

        result = self.synergy.submit_probability(
            market_id,
            probability,
            confidence=0.8,
            notes=notes or f"Yair estimate at {datetime.now().strftime('%H:%M')}"
        )

        # Wire to live nexus
        from integrafix.human_machine_synergy import wire_wisdom_to_live_nexus
        wire_wisdom_to_live_nexus()

        return f"Recorded: {market_id[:30]}... = {probability:.0%}"

    def approve(self, request_id: str) -> str:
        """
        Approve a pending trade.

        Usage: yair approve REQUEST_ID
        """
        result = self.synergy.approve_trade(request_id, approved=True)
        return f"Approved: {result.get('status', 'error')}"

    def reject(self, request_id: str, reason: str = "") -> str:
        """
        Reject a pending trade.

        Usage: yair reject REQUEST_ID "Reason"
        """
        result = self.synergy.approve_trade(request_id, approved=False, notes=reason)
        return f"Rejected: {result.get('status', 'error')}"

    def run(self, dry_run: bool = True) -> str:
        """
        Run full ABCFC cycle.

        Usage: yair run [--live]
        """
        self.orchestrator.dry_run = dry_run

        result = self.orchestrator.run_cycle()

        lines = [
            "=" * 60,
            f"ABCFC CYCLE {'(DRY RUN)' if dry_run else '(LIVE)'}",
            "=" * 60,
            f"\nHierarchy: {result['state']['hierarchy_nodes']} nodes",
            f"Sources: {', '.join(result['state']['sources'])}",
            f"\nDecision: {result['decision']['action']} on {result['decision']['target_node']}",
            f"Rationale: {result['rationale']}",
            f"\nExecution: {result['result']['status']}",
        ]

        return "\n".join(lines)

    def opportunities(self) -> str:
        """
        Show current market opportunities.

        Usage: yair opportunities
        """
        opps = self.synergy.scan_markets()

        lines = [
            "=" * 60,
            f"MARKET OPPORTUNITIES ({len(opps)} found)",
            "=" * 60,
        ]

        for i, opp in enumerate(opps[:10], 1):
            lines.append(f"\n[{i}] {opp['question'][:55]}")
            lines.append(f"    Market: {opp['market_price']:.0%} | Our: {opp['our_estimate']:.0%}")
            lines.append(f"    Edge: {opp['edge']:.1%} ({opp['edge_source']})")
            if opp.get('needs_human_input'):
                lines.append(f"    → NEEDS YOUR ESTIMATE")
                lines.append(f"      yair estimate '{opp['market_id'][:30]}' 0.XX")

        lines.append("\n" + "=" * 60)
        return "\n".join(lines)

    def help(self) -> str:
        """Show available commands."""
        return """
YAIR SIEGEL INTERFACE - COMMANDS
================================

Quick Commands:
  yair status         - Quick status (what to know now)
  yair review         - Items needing your input
  yair opportunities  - Current market opportunities
  yair run            - Run ABCFC cycle (dry run)
  yair run --live     - Run ABCFC cycle (real execution)

Human Input:
  yair estimate MARKET 0.65       - Submit probability estimate
  yair estimate MARKET 0.65 "Why" - With notes
  yair approve REQUEST_ID         - Approve pending trade
  yair reject REQUEST_ID          - Reject pending trade

Examples:
  yair estimate 'will-bitcoin-reach-105000' 0.55 'Think it will hit'
  yair approve prob_bitcoin_12345

Machine Handles (24/7):
  - Market scanning
  - Position sizing
  - Trade execution
  - Monitoring

You Provide (when convenient):
  - Probability estimates
  - Trade approvals (large)
  - Strategy direction
"""


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    import sys

    interface = YairInterface()

    if len(sys.argv) < 2:
        print(interface.help())
        return

    command = sys.argv[1].lower()

    if command == "status":
        print(interface.status())

    elif command == "review":
        print(interface.review())

    elif command == "opportunities":
        print(interface.opportunities())

    elif command == "estimate":
        if len(sys.argv) < 4:
            print("Usage: yair estimate MARKET_ID PROBABILITY [NOTES]")
            return
        market_id = sys.argv[2]
        prob = float(sys.argv[3])
        notes = sys.argv[4] if len(sys.argv) > 4 else ""
        print(interface.estimate(market_id, prob, notes))

    elif command == "approve":
        if len(sys.argv) < 3:
            print("Usage: yair approve REQUEST_ID")
            return
        print(interface.approve(sys.argv[2]))

    elif command == "reject":
        if len(sys.argv) < 3:
            print("Usage: yair reject REQUEST_ID [REASON]")
            return
        reason = sys.argv[3] if len(sys.argv) > 3 else ""
        print(interface.reject(sys.argv[2], reason))

    elif command == "run":
        live = "--live" in sys.argv
        print(interface.run(dry_run=not live))

    elif command == "help":
        print(interface.help())

    else:
        print(f"Unknown command: {command}")
        print(interface.help())


if __name__ == "__main__":
    main()
