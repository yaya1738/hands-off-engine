#!/usr/bin/env python3
"""
🏗️ ARCHITECTURE SESSION - Deep Thinking on Hard Problems
Serving: Yair Siegel

Convenes system architects to think through complex design problems.
Not monitoring. Not execution. Pure design thinking.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
SESSION_LOG = STATE_DIR / "architecture_sessions.jsonl"

@dataclass
class Architect:
    """An architect perspective."""
    name: str
    role: str
    thinking_style: str

    def think(self, problem: str, context: Dict) -> Dict:
        """Generate architectural thinking on a problem."""
        return {
            "architect": self.name,
            "role": self.role,
            "analysis": self._analyze(problem, context),
            "proposals": self._propose(problem, context),
            "concerns": self._concerns(problem, context),
        }

    def _analyze(self, problem: str, context: Dict) -> str:
        """Analyze the problem from this architect's perspective."""
        raise NotImplementedError

    def _propose(self, problem: str, context: Dict) -> List[str]:
        """Propose solutions."""
        raise NotImplementedError

    def _concerns(self, problem: str, context: Dict) -> List[str]:
        """Raise concerns."""
        raise NotImplementedError


class SystemsArchitect(Architect):
    """Thinks about system structure and flow."""

    def __init__(self):
        super().__init__(
            name="Systems Architect",
            role="Structure & Flow",
            thinking_style="How do components connect and data flow?"
        )

    def _analyze(self, problem: str, context: Dict) -> str:
        if "power" in problem.lower() or "generat" in problem.lower():
            return """
POWER GENERATION ANALYSIS:
A power plant converts INPUT → OUTPUT continuously.

Current system inputs available:
- Compute cycles (droplets running 24/7)
- AI inference (Claude API - costs money)
- Trading infrastructure (Polymarket - needs capital)
- Web traffic (minimal - 85 visitors, 0 conversions)
- Cron jobs (running continuously)

Current system outputs:
- Monitoring data (no value)
- State files (no value)
- Alerts (no value)
- Trading signals (potential value, not executed)

GAP: We have inputs but no value-producing outputs.
The power plant must bridge this gap.
"""
        return f"Analyzing: {problem}"

    def _propose(self, problem: str, context: Dict) -> List[str]:
        if "power" in problem.lower():
            return [
                "PROPOSAL 1: Trading Loop - Use free compute to analyze markets, execute when capital available, profits feed back",
                "PROPOSAL 2: Content Factory - Generate valuable content (analysis, reports) that can be monetized",
                "PROPOSAL 3: Service Engine - Package AI capabilities as automated services (audits, analysis)",
                "PROPOSAL 4: Arbitrage Engine - Find price differences across platforms, execute trades",
            ]
        return ["Need more context"]

    def _concerns(self, problem: str, context: Dict) -> List[str]:
        return [
            "Most generation requires initial capital or API credits",
            "Free compute alone doesn't generate value without intelligence",
            "Need external demand/market to sell outputs",
        ]


class EconomicsArchitect(Architect):
    """Thinks about value flows and economics."""

    def __init__(self):
        super().__init__(
            name="Economics Architect",
            role="Value & Incentives",
            thinking_style="Where does value come from and go?"
        )

    def _analyze(self, problem: str, context: Dict) -> str:
        if "power" in problem.lower():
            balance = context.get("balance", 8.99)
            return f"""
ECONOMIC ANALYSIS:
Current balance: ${balance}
Current income: $0/day
Current burn: ~$12/month (infrastructure)

Value sources in reach:
1. TRADING: Need $50+ to start meaningfully
2. CONSULTING: Need clients (0 currently)
3. BOUNTIES: GitHub sponsors, bug bounties
4. ARBITRAGE: Need capital + speed

The ONLY free value generation:
- Knowledge arbitrage (know something others don't)
- Time arbitrage (do something faster than others)
- Attention arbitrage (get eyes on something valuable)

Power plant must generate from what we HAVE, not what we NEED.
"""
        return f"Economic view: {problem}"

    def _propose(self, problem: str, context: Dict) -> List[str]:
        if "power" in problem.lower():
            return [
                "PROPOSAL: Signal-as-Power - Trading signals ARE the generation, execution is separate",
                "PROPOSAL: Knowledge Extraction - Mine the codebase for packageable insights",
                "PROPOSAL: Attention Capture - Generate content that attracts paying customers",
                "PROPOSAL: Micro-work - Break down capabilities into tiny sellable units",
            ]
        return []

    def _concerns(self, problem: str, context: Dict) -> List[str]:
        return [
            "Bootstrap paradox: Need money to make money",
            "Cold start: No reputation, no customers",
            "Time cost: Human attention is the scarcest resource",
        ]


class PragmatistArchitect(Architect):
    """Thinks about what's actually buildable now."""

    def __init__(self):
        super().__init__(
            name="Pragmatist Architect",
            role="Reality Check",
            thinking_style="What can we actually build today?"
        )

    def _analyze(self, problem: str, context: Dict) -> str:
        if "power" in problem.lower():
            return """
PRAGMATIC ANALYSIS:
What we CAN do right now with $0:

1. CRON JOBS ARE RUNNING
   - 11 scheduled tasks executing continuously
   - This IS work being done
   - But outputs have no external value

2. TRADING INFRASTRUCTURE EXISTS
   - Polymarket connected
   - Signals being generated
   - Only need capital to execute

3. WEB PRESENCE EXISTS
   - Landing pages live
   - Just need traffic → conversion

4. AI CAPABILITIES EXIST
   - Can generate analysis, reports, code
   - Need to package and sell

REAL POWER PLANT OPTIONS:
A) Wait for position resolution (~$98 coming)
B) Generate sellable content NOW
C) Find free money (bounties, grants, airdrops)
"""
        return f"Pragmatic view: {problem}"

    def _propose(self, problem: str, context: Dict) -> List[str]:
        if "power" in problem.lower():
            return [
                "CONCRETE: Trading signal generator as the 'turbine' - runs on compute, outputs signals",
                "CONCRETE: Position resolver as 'fuel intake' - converts resolved positions to capital",
                "CONCRETE: Outreach engine as 'grid connection' - connects generated value to buyers",
                "CONCRETE: The power plant IS the trading loop - signals → execution → profit → more signals",
            ]
        return []

    def _concerns(self, problem: str, context: Dict) -> List[str]:
        return [
            "We're overthinking - the trading loop IS the power plant",
            "Just need the $50 threshold to start the generator",
            "Abstract designs don't pay bills",
        ]


class ArchitectureSession:
    """Convenes architects to think through a problem."""

    def __init__(self):
        self.architects = [
            SystemsArchitect(),
            EconomicsArchitect(),
            PragmatistArchitect(),
        ]
        self.sessions: List[Dict] = []

    def convene(self, problem: str, context: Dict = None) -> Dict:
        """Run an architecture session on a problem."""
        context = context or {}

        # Gather current system state for context
        context.update(self._gather_context())

        session = {
            "session_id": datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "problem": problem,
            "context": context,
            "perspectives": [],
            "synthesis": None,
        }

        # Each architect thinks
        for architect in self.architects:
            perspective = architect.think(problem, context)
            session["perspectives"].append(perspective)

        # Synthesize
        session["synthesis"] = self._synthesize(session["perspectives"])

        # Log
        self._log_session(session)

        return session

    def _gather_context(self) -> Dict:
        """Gather current system context."""
        context = {}

        # Financial state
        try:
            finance_file = STATE_DIR / "financial_state.json"
            if finance_file.exists():
                fin = json.loads(finance_file.read_text())
                context["balance"] = fin.get("balance", 0)
                context["positions"] = fin.get("positions_value", 0)
        except:
            context["balance"] = 8.99
            context["positions"] = 98.05

        # System health
        try:
            health_file = STATE_DIR / "doctor_state.json"
            if health_file.exists():
                health = json.loads(health_file.read_text())
                context["health_score"] = health.get("health_score", 0)
        except:
            pass

        return context

    def _synthesize(self, perspectives: List[Dict]) -> Dict:
        """Synthesize architectural perspectives into recommendations."""
        all_proposals = []
        all_concerns = []

        for p in perspectives:
            all_proposals.extend(p.get("proposals", []))
            all_concerns.extend(p.get("concerns", []))

        # Find common themes
        synthesis = {
            "key_insight": "The power plant must convert existing resources (compute, infrastructure) into real value",
            "recommended_approach": None,
            "all_proposals": all_proposals,
            "all_concerns": all_concerns,
            "decision_needed": [],
        }

        # Check for convergence
        trading_votes = sum(1 for p in all_proposals if "trading" in p.lower())
        content_votes = sum(1 for p in all_proposals if "content" in p.lower())
        service_votes = sum(1 for p in all_proposals if "service" in p.lower())

        if trading_votes >= 2:
            synthesis["recommended_approach"] = "TRADING_LOOP"
            synthesis["rationale"] = "Multiple architects converge on trading as the power generation mechanism"
        elif content_votes >= 2:
            synthesis["recommended_approach"] = "CONTENT_FACTORY"
        elif service_votes >= 2:
            synthesis["recommended_approach"] = "SERVICE_ENGINE"
        else:
            synthesis["decision_needed"] = [
                "No architectural consensus - need human decision",
                "Options: Trading Loop, Content Factory, Service Engine, Hybrid"
            ]

        return synthesis

    def _log_session(self, session: Dict):
        """Log the architecture session."""
        with open(SESSION_LOG, "a") as f:
            f.write(json.dumps(session) + "\n")

    def display_session(self, session: Dict):
        """Display session results."""
        print(f"\n🏗️  ARCHITECTURE SESSION: {session['session_id']}")
        print("=" * 70)
        print(f"PROBLEM: {session['problem']}")
        print(f"CONTEXT: Balance=${session['context'].get('balance', '?')}, Positions=${session['context'].get('positions', '?')}")
        print()

        for p in session["perspectives"]:
            print(f"\n{'─' * 70}")
            print(f"👷 {p['architect']} ({p['role']})")
            print(f"{'─' * 70}")
            print(p["analysis"])
            print("\nPROPOSALS:")
            for prop in p["proposals"]:
                print(f"  • {prop}")
            print("\nCONCERNS:")
            for concern in p["concerns"]:
                print(f"  ⚠ {concern}")

        print(f"\n{'=' * 70}")
        print("🎯 SYNTHESIS")
        print("=" * 70)
        synth = session["synthesis"]
        print(f"Key Insight: {synth['key_insight']}")
        if synth["recommended_approach"]:
            print(f"Recommended: {synth['recommended_approach']}")
            print(f"Rationale: {synth.get('rationale', 'N/A')}")
        if synth["decision_needed"]:
            print("\n⚠️  DECISION NEEDED:")
            for d in synth["decision_needed"]:
                print(f"  {d}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Architecture Session")
    parser.add_argument("command", choices=["convene", "power-plant"], nargs="?", default="power-plant")
    parser.add_argument("--problem", help="Problem to discuss")
    args = parser.parse_args()

    session = ArchitectureSession()

    if args.command == "convene" and args.problem:
        result = session.convene(args.problem)
        session.display_session(result)
    elif args.command == "power-plant":
        result = session.convene(
            "Design a NON-ABSTRACT power plant that generates REAL work/value for the system continuously"
        )
        session.display_session(result)


if __name__ == "__main__":
    main()
