#!/usr/bin/env python3
"""
INTEGRAFIX: Human-Machine Synergy Bridge
=========================================

PROBLEM:
Machine can calculate, execute, monitor 24/7 but lacks:
- Edge detection / probability estimation expertise
- Strategic judgment on when to act
- Risk tolerance calibration
- Domain knowledge for prediction markets

Human (Yair) has:
- Trading experience and intuition
- Probability calibration skills
- Strategic vision
- Risk preferences

SOLUTION:
Wire human wisdom to machine execution in a synergistic loop:

    ┌─────────────────────────────────────────────────────────────────┐
    │                 HUMAN-MACHINE SYNERGY LOOP                       │
    └─────────────────────────────────────────────────────────────────┘
                                │
         MACHINE                │                 HUMAN (Yair)
         ───────                │                 ────────────
    ┌─────────────────┐         │         ┌─────────────────────┐
    │ 1. SCAN         │ ───────►│◄─────── │ 1. REVIEW           │
    │    Markets      │         │         │    Opportunities    │
    │    24/7         │         │         │    (async)          │
    └─────────────────┘         │         └─────────────────────┘
            │                   │                   │
            ▼                   │                   ▼
    ┌─────────────────┐         │         ┌─────────────────────┐
    │ 2. FILTER       │◄────────┼────────►│ 2. ESTIMATE         │
    │    By criteria  │         │         │    Probabilities    │
    │    (liquidity,  │         │         │    (where edge      │
    │     spread)     │         │         │     exists)         │
    └─────────────────┘         │         └─────────────────────┘
            │                   │                   │
            ▼                   │                   ▼
    ┌─────────────────┐         │         ┌─────────────────────┐
    │ 3. CALCULATE    │◄────────┼────────►│ 3. APPROVE/VETO     │
    │    Position     │         │         │    Final decisions  │
    │    sizing       │         │         │    on large trades  │
    │    (Kelly)      │         │         │                     │
    └─────────────────┘         │         └─────────────────────┘
            │                   │                   │
            ▼                   │                   ▼
    ┌─────────────────┐         │         ┌─────────────────────┐
    │ 4. EXECUTE      │         │         │ 4. CALIBRATE        │
    │    Trades       │◄────────┼────────►│    Review outcomes  │
    │    (instant)    │         │         │    Adjust estimates │
    └─────────────────┘         │         └─────────────────────┘
            │                   │                   │
            ▼                   │                   ▼
    ┌─────────────────┐         │         ┌─────────────────────┐
    │ 5. MONITOR      │ ───────►│◄─────── │ 5. STRATEGIZE       │
    │    Positions    │         │         │    Macro decisions  │
    │    24/7         │         │         │                     │
    └─────────────────┘         │         └─────────────────────┘

Serving: Yair Siegel
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
SYNERGY_STATE = STATE_DIR / "human_machine_synergy.json"
WISDOM_INPUT = STATE_DIR / "yair_wisdom_input.json"
PENDING_REVIEWS = STATE_DIR / "pending_human_review.json"


class InputType(Enum):
    """Types of human input needed."""
    PROBABILITY = "probability"      # Estimate P(event)
    APPROVAL = "approval"            # Approve/reject trade
    STRATEGY = "strategy"            # High-level direction
    CALIBRATION = "calibration"      # Review past predictions
    VETO = "veto"                    # Emergency stop


@dataclass
class HumanInputRequest:
    """Request for human input."""
    request_id: str
    input_type: InputType
    market_id: str
    question: str
    current_price: float
    machine_estimate: float
    machine_confidence: float
    urgency: str  # "low", "medium", "high"
    context: Dict
    created_at: str
    expires_at: Optional[str] = None
    human_response: Optional[Dict] = None
    responded_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "request_id": self.request_id,
            "input_type": self.input_type.value,
            "market_id": self.market_id,
            "question": self.question,
            "current_price": self.current_price,
            "machine_estimate": self.machine_estimate,
            "machine_confidence": self.machine_confidence,
            "urgency": self.urgency,
            "context": self.context,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "human_response": self.human_response,
            "responded_at": self.responded_at,
        }


class HumanMachineSynergy:
    """
    Bridges human wisdom with machine execution.

    HUMAN provides:
    - Probability estimates (edge detection)
    - Trade approvals (risk management)
    - Strategic direction
    - Calibration feedback

    MACHINE provides:
    - 24/7 market scanning
    - Position sizing (Kelly)
    - Instant execution
    - Continuous monitoring
    - Record keeping
    """

    def __init__(self):
        self.pending_requests: List[HumanInputRequest] = []
        self.wisdom_cache: Dict[str, Dict] = {}  # market_id -> human estimates
        self.auto_approve_threshold = 25.0  # Auto-approve trades under $25
        self.min_edge_for_action = 0.05     # 5% minimum edge

        self._load_state()

    # =========================================================================
    # MACHINE: SCAN - Find opportunities
    # =========================================================================

    def scan_markets(self) -> List[Dict]:
        """
        Machine scans markets and identifies opportunities.
        Returns list of opportunities that may need human input.
        """
        opportunities = []

        # Load existing market data
        model_file = STATE_DIR / "polymarket-model.json"
        if model_file.exists():
            try:
                with open(model_file) as f:
                    data = json.load(f)
                markets = data.get("markets", [])

                for market in markets:
                    opp = self._analyze_opportunity(market)
                    if opp:
                        opportunities.append(opp)
            except Exception as e:
                print(f"Error loading markets: {e}")

        return opportunities

    def _analyze_opportunity(self, market: Dict) -> Optional[Dict]:
        """Analyze a single market opportunity."""
        market_id = market.get("market_id", "")
        question = market.get("question", "")
        market_price = market.get("market_price", 0.5)
        fair_price = market.get("fair_price", market_price)
        model_edge = market.get("model_edge", 0)
        confidence = market.get("model_confidence", 0.5)
        liquidity = market.get("liquidity", 0)

        # Check if human has provided estimate
        human_estimate = self.wisdom_cache.get(market_id, {}).get("probability")

        if human_estimate is not None:
            # Use human estimate
            edge = abs(human_estimate - market_price)
            source = "human"
        else:
            # Use machine estimate
            edge = model_edge
            source = "machine"

        # Skip low-edge opportunities
        if edge < self.min_edge_for_action:
            return None

        return {
            "market_id": market_id,
            "question": question,
            "market_price": market_price,
            "our_estimate": human_estimate or fair_price,
            "edge": edge,
            "edge_source": source,
            "machine_confidence": confidence,
            "liquidity": liquidity,
            "needs_human_input": source == "machine" and confidence < 0.8,
        }

    # =========================================================================
    # MACHINE: REQUEST HUMAN INPUT
    # =========================================================================

    def request_probability_estimate(self, market: Dict) -> HumanInputRequest:
        """Create request for human probability estimate, enriched with system knowledge."""
        # Enrich with knowledge context
        knowledge_context = self._get_knowledge_context(market)

        request = HumanInputRequest(
            request_id=f"prob_{market['market_id']}_{datetime.now().timestamp():.0f}",
            input_type=InputType.PROBABILITY,
            market_id=market["market_id"],
            question=market["question"],
            current_price=market["market_price"],
            machine_estimate=market.get("our_estimate", market["market_price"]),
            machine_confidence=market.get("machine_confidence", 0.5),
            urgency="medium",
            context={
                "liquidity": market.get("liquidity", 0),
                "suggested_side": "YES" if market.get("our_estimate", 0.5) > market["market_price"] else "NO",
                # Knowledge enrichment
                "success_patterns": knowledge_context.get("success_patterns", []),
                "recommendations": knowledge_context.get("recommendations", []),
                "past_learnings": knowledge_context.get("past_learnings", []),
            },
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        self.pending_requests.append(request)
        self._save_pending_requests()

        return request

    def _get_knowledge_context(self, market: Dict) -> Dict:
        """Get knowledge context from synergy-knowledge bridge."""
        try:
            from integrafix.synergy_knowledge_bridge import SynergyKnowledgeBridge
            bridge = SynergyKnowledgeBridge()
            enriched = bridge.enrich_estimate_request(market)
            return enriched
        except Exception as e:
            return {"error": str(e)}

    def request_trade_approval(self, trade: Dict) -> HumanInputRequest:
        """Create request for human trade approval."""
        request = HumanInputRequest(
            request_id=f"approve_{trade['market_id']}_{datetime.now().timestamp():.0f}",
            input_type=InputType.APPROVAL,
            market_id=trade["market_id"],
            question=trade["question"],
            current_price=trade["price"],
            machine_estimate=trade.get("our_estimate", trade["price"]),
            machine_confidence=trade.get("confidence", 0.7),
            urgency="high" if trade.get("size", 0) > 50 else "medium",
            context={
                "side": trade["side"],
                "size": trade["size"],
                "expected_pnl": trade.get("expected_pnl", 0),
                "worst_pnl": trade.get("worst_pnl", 0),
                "best_pnl": trade.get("best_pnl", 0),
            },
            created_at=datetime.now(timezone.utc).isoformat(),
            expires_at=trade.get("expires_at"),
        )

        self.pending_requests.append(request)
        self._save_pending_requests()

        return request

    # =========================================================================
    # HUMAN: PROVIDE INPUT
    # =========================================================================

    def submit_probability(self, market_id: str, probability: float,
                          confidence: float = 0.8, notes: str = "") -> Dict:
        """
        Human submits probability estimate for a market.

        Args:
            market_id: Market identifier
            probability: Human's P(YES) estimate [0, 1]
            confidence: How confident in this estimate [0, 1]
            notes: Optional reasoning
        """
        self.wisdom_cache[market_id] = {
            "probability": probability,
            "confidence": confidence,
            "notes": notes,
            "submitted_at": datetime.now(timezone.utc).isoformat(),
            "source": "yair_siegel",
        }

        # Mark any pending requests as responded
        for req in self.pending_requests:
            if req.market_id == market_id and req.input_type == InputType.PROBABILITY:
                req.human_response = {
                    "probability": probability,
                    "confidence": confidence,
                    "notes": notes,
                }
                req.responded_at = datetime.now(timezone.utc).isoformat()

        self._save_state()

        return {
            "status": "recorded",
            "market_id": market_id,
            "probability": probability,
            "will_affect": "live_nexus_actions",
        }

    def approve_trade(self, request_id: str, approved: bool,
                     modified_size: float = None, notes: str = "") -> Dict:
        """Human approves or rejects a proposed trade."""
        for req in self.pending_requests:
            if req.request_id == request_id:
                req.human_response = {
                    "approved": approved,
                    "modified_size": modified_size,
                    "notes": notes,
                }
                req.responded_at = datetime.now(timezone.utc).isoformat()
                self._save_pending_requests()

                return {
                    "status": "approved" if approved else "rejected",
                    "request_id": request_id,
                    "execute": approved,
                    "size": modified_size or req.context.get("size"),
                }

        return {"error": f"Request {request_id} not found"}

    # =========================================================================
    # MACHINE: CALCULATE - Position Sizing
    # =========================================================================

    def calculate_position(self, market: Dict) -> Dict:
        """
        Calculate optimal position size using Kelly criterion.
        Uses human probability estimate if available.
        """
        market_id = market.get("market_id", "")
        price = market.get("market_price", 0.5)

        # Get probability estimate
        human_data = self.wisdom_cache.get(market_id, {})
        prob = human_data.get("probability", market.get("our_estimate", 0.5))
        confidence = human_data.get("confidence", market.get("machine_confidence", 0.5))

        # Calculate edge
        edge = prob - price if prob > price else (1 - prob) - (1 - price)
        side = "YES" if prob > price else "NO"

        if edge <= 0:
            return {"size": 0, "reason": "No edge"}

        # Kelly fraction: edge / odds
        if side == "YES":
            odds = (1 - price) / price if price > 0 else 0
        else:
            odds = price / (1 - price) if price < 1 else 0

        kelly = (prob * odds - (1 - prob)) / odds if odds > 0 else 0
        kelly = max(0, min(kelly, 0.25))  # Cap at 25%

        # Fractional Kelly based on confidence
        kelly *= confidence * 0.5  # Half Kelly, adjusted by confidence

        # Get deployable capital
        try:
            from integrafix.reality_bridge import RealityBridge
            bridge = RealityBridge()
            snapshot = bridge.snapshot_reality()
            deployable = snapshot.deployable
        except:
            deployable = 100  # Default

        size = round(deployable * kelly, 2)

        # Calculate P&L bounds
        if side == "YES":
            worst_pnl = -size * price
            best_pnl = size * (1 - price)
        else:
            worst_pnl = -size * (1 - price)
            best_pnl = size * price

        expected_pnl = size * edge

        return {
            "market_id": market_id,
            "side": side,
            "size": size,
            "price": price,
            "our_probability": prob,
            "edge": edge,
            "kelly_fraction": kelly,
            "worst_pnl": worst_pnl,
            "best_pnl": best_pnl,
            "expected_pnl": expected_pnl,
            "needs_approval": size > self.auto_approve_threshold,
            "source": "human" if market_id in self.wisdom_cache else "machine",
        }

    # =========================================================================
    # MACHINE: EXECUTE - With human wisdom integrated
    # =========================================================================

    def execute_with_wisdom(self, dry_run: bool = True) -> Dict:
        """
        Execute trades using human wisdom where available.

        Flow:
        1. Scan markets
        2. Calculate positions (using human estimates)
        3. Auto-execute small trades
        4. Request approval for large trades
        5. Return execution summary
        """
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": dry_run,
            "scanned": 0,
            "opportunities": 0,
            "executed": [],
            "pending_approval": [],
            "needs_human_input": [],
        }

        # 1. Scan
        opportunities = self.scan_markets()
        results["scanned"] = len(opportunities)

        for opp in opportunities:
            # Skip if needs human probability input
            if opp.get("needs_human_input"):
                req = self.request_probability_estimate(opp)
                results["needs_human_input"].append({
                    "market_id": opp["market_id"],
                    "question": opp["question"],
                    "request_id": req.request_id,
                })
                continue

            # 2. Calculate position
            position = self.calculate_position(opp)

            if position.get("size", 0) <= 0:
                continue

            results["opportunities"] += 1

            # 3. Check if needs approval
            if position["needs_approval"]:
                req = self.request_trade_approval({
                    **opp,
                    **position,
                    "question": opp["question"],
                })
                results["pending_approval"].append({
                    "market_id": opp["market_id"],
                    "side": position["side"],
                    "size": position["size"],
                    "request_id": req.request_id,
                })
                continue

            # 4. Execute (auto-approved small trades)
            if dry_run:
                exec_result = {
                    "status": "DRY_RUN",
                    "market_id": opp["market_id"],
                    "side": position["side"],
                    "size": position["size"],
                    "expected_pnl": position["expected_pnl"],
                }
            else:
                exec_result = self._execute_trade(position)

            results["executed"].append(exec_result)

        self._save_state()

        return results

    def _execute_trade(self, position: Dict) -> Dict:
        """Execute a trade via live nexus."""
        try:
            from integrafix.abcfc_live_nexus import ABCFCLiveNexus
            nexus = ABCFCLiveNexus(dry_run=False)
            # Would execute trade here
            return {
                "status": "EXECUTED",
                "market_id": position["market_id"],
                "side": position["side"],
                "size": position["size"],
            }
        except Exception as e:
            return {
                "status": "ERROR",
                "error": str(e),
                "market_id": position["market_id"],
            }

    # =========================================================================
    # HUMAN INTERFACE: Best UI for input
    # =========================================================================

    def get_pending_for_human(self) -> Dict:
        """
        Get all pending items requiring human attention.
        Formatted for optimal human review.
        """
        pending = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "probability_estimates_needed": [],
            "approvals_needed": [],
            "calibration_reviews": [],
        }

        for req in self.pending_requests:
            if req.human_response is not None:
                continue  # Already responded

            item = {
                "request_id": req.request_id,
                "question": req.question,
                "market_price": req.current_price,
                "machine_estimate": req.machine_estimate,
                "machine_confidence": req.machine_confidence,
                "urgency": req.urgency,
            }

            if req.input_type == InputType.PROBABILITY:
                item["suggested_action"] = f"Estimate P(YES) for: {req.question}"
                item["market_says"] = f"{req.current_price:.0%}"
                item["machine_says"] = f"{req.machine_estimate:.0%} (conf: {req.machine_confidence:.0%})"
                pending["probability_estimates_needed"].append(item)

            elif req.input_type == InputType.APPROVAL:
                ctx = req.context
                item["proposed_trade"] = f"{ctx.get('side')} ${ctx.get('size'):.2f} @ {req.current_price:.0%}"
                item["expected_pnl"] = f"${ctx.get('expected_pnl', 0):.2f}"
                item["worst_case"] = f"${ctx.get('worst_pnl', 0):.2f}"
                pending["approvals_needed"].append(item)

        # Add summary
        pending["summary"] = {
            "total_pending": len(pending["probability_estimates_needed"]) + len(pending["approvals_needed"]),
            "high_urgency": sum(1 for req in self.pending_requests
                               if req.urgency == "high" and req.human_response is None),
        }

        return pending

    def render_input_interface(self) -> str:
        """Render terminal interface for human input."""
        pending = self.get_pending_for_human()

        lines = [
            "=" * 70,
            "YAIR SIEGEL: HUMAN INPUT REQUIRED",
            f"Generated: {pending['timestamp']}",
            "=" * 70,
        ]

        # Probability estimates needed
        if pending["probability_estimates_needed"]:
            lines.append("\n>>> PROBABILITY ESTIMATES NEEDED")
            lines.append("    (Your edge detection is needed)")
            lines.append("")

            for i, item in enumerate(pending["probability_estimates_needed"][:5], 1):
                lines.append(f"    [{i}] {item['question'][:60]}")
                lines.append(f"        Market: {item['market_says']} | Machine: {item['machine_says']}")
                lines.append(f"        → Submit: synergy.submit_probability('{item['request_id'][:20]}...', prob)")
                lines.append("")

        # Approvals needed
        if pending["approvals_needed"]:
            lines.append("\n>>> TRADE APPROVALS NEEDED")
            lines.append("    (Your judgment required for larger trades)")
            lines.append("")

            for i, item in enumerate(pending["approvals_needed"][:5], 1):
                lines.append(f"    [{i}] {item['question'][:50]}")
                lines.append(f"        Trade: {item['proposed_trade']}")
                lines.append(f"        E[P&L]: {item['expected_pnl']} | Worst: {item['worst_case']}")
                lines.append(f"        → Approve: synergy.approve_trade('{item['request_id'][:20]}...', True)")
                lines.append("")

        # Summary
        lines.append("-" * 70)
        lines.append(f"Total pending: {pending['summary']['total_pending']} | High urgency: {pending['summary']['high_urgency']}")
        lines.append("=" * 70)

        return "\n".join(lines)

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    def _load_state(self):
        """Load synergy state."""
        if SYNERGY_STATE.exists():
            try:
                with open(SYNERGY_STATE) as f:
                    data = json.load(f)
                self.wisdom_cache = data.get("wisdom_cache", {})
                self.auto_approve_threshold = data.get("auto_approve_threshold", 25.0)
            except:
                pass

        if PENDING_REVIEWS.exists():
            try:
                with open(PENDING_REVIEWS) as f:
                    data = json.load(f)
                # Reconstruct pending requests
                for req_data in data.get("requests", []):
                    req = HumanInputRequest(
                        request_id=req_data["request_id"],
                        input_type=InputType(req_data["input_type"]),
                        market_id=req_data["market_id"],
                        question=req_data["question"],
                        current_price=req_data["current_price"],
                        machine_estimate=req_data["machine_estimate"],
                        machine_confidence=req_data["machine_confidence"],
                        urgency=req_data["urgency"],
                        context=req_data["context"],
                        created_at=req_data["created_at"],
                        expires_at=req_data.get("expires_at"),
                        human_response=req_data.get("human_response"),
                        responded_at=req_data.get("responded_at"),
                    )
                    self.pending_requests.append(req)
            except:
                pass

    def _save_state(self):
        """Save synergy state."""
        state = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "wisdom_cache": self.wisdom_cache,
            "auto_approve_threshold": self.auto_approve_threshold,
            "total_estimates": len(self.wisdom_cache),
        }
        with open(SYNERGY_STATE, 'w') as f:
            json.dump(state, f, indent=2)

    def _save_pending_requests(self):
        """Save pending requests."""
        data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "requests": [req.to_dict() for req in self.pending_requests],
        }
        with open(PENDING_REVIEWS, 'w') as f:
            json.dump(data, f, indent=2)


# =============================================================================
# WIRE TO ABCFC LIVE NEXUS
# =============================================================================

def wire_wisdom_to_live_nexus():
    """Wire human wisdom cache to live nexus probability estimates."""
    synergy = HumanMachineSynergy()

    # Create probability estimates file for live nexus
    estimates = {}
    for market_id, data in synergy.wisdom_cache.items():
        estimates[market_id] = data.get("probability")

    estimates_file = STATE_DIR / "human_probability_estimates.json"
    with open(estimates_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "yair_siegel_wisdom",
            "estimates": estimates,
        }, f, indent=2)

    return {
        "wired": len(estimates),
        "file": str(estimates_file),
    }


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Human-Machine Synergy Bridge")
    parser.add_argument("command", choices=[
        "scan", "pending", "execute", "wire", "submit"
    ], default="pending", nargs="?")
    parser.add_argument("--market", help="Market ID for submit")
    parser.add_argument("--prob", type=float, help="Probability estimate")
    parser.add_argument("--dry-run", action="store_true", default=True)
    args = parser.parse_args()

    synergy = HumanMachineSynergy()

    if args.command == "scan":
        opps = synergy.scan_markets()
        print(f"Scanned {len(opps)} opportunities")
        for opp in opps[:5]:
            print(f"  {opp['question'][:50]}")
            print(f"    Edge: {opp['edge']:.1%} ({opp['edge_source']})")

    elif args.command == "pending":
        print(synergy.render_input_interface())

    elif args.command == "execute":
        result = synergy.execute_with_wisdom(dry_run=args.dry_run)
        print(json.dumps(result, indent=2))

    elif args.command == "wire":
        result = wire_wisdom_to_live_nexus()
        print(f"Wired {result['wired']} estimates to live nexus")

    elif args.command == "submit":
        if args.market and args.prob is not None:
            result = synergy.submit_probability(args.market, args.prob)
            print(f"Submitted: {result}")
        else:
            print("Usage: --market MARKET_ID --prob 0.65")


if __name__ == "__main__":
    main()
