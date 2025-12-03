#!/usr/bin/env python3
"""
HFT Execution Bridge - Connect Opportunity Detection to HFT Execution

This module bridges the gap between:
- Knowledge Fusion (insights)
- Yair Wisdom Engine (opportunities)
- HFT Infrastructure (execution)

THE MISSING LINK: Knowledge → Execution

USAGE:
    from autonomous.hft_execution_bridge import hft_bridge

    # Scan for opportunities and execute
    results = hft_bridge.scan_and_execute()

    # Or use in backend loop
    hft_status = hft_bridge.run_hft_cycle()

Serving: Yair Siegel
"""

import os
import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"


@dataclass
class ExecutionOpportunity:
    """Represents a trading opportunity ready for execution."""
    opportunity_type: str  # merge_arb, espn_signal, thin_book, grid_capture
    token_id: str
    side: str  # BUY, SELL, BOTH
    price: float
    size: float
    confidence: float
    source: str  # yair_wisdom, knowledge_fusion, market_scan
    reason: str


@dataclass
class ExecutionResult:
    """Result of executing an opportunity."""
    success: bool
    opportunity: ExecutionOpportunity
    orders_placed: int
    latency_ms: float
    error: Optional[str] = None


class HFTExecutionBridge:
    """
    Bridge between opportunity detection and HFT execution.

    Connects:
    - Yair Wisdom Engine → Detects opportunities
    - Knowledge Fusion → Provides context
    - HFT Agent API → Executes trades
    """

    def __init__(self):
        self._hft = None
        self._wisdom = None
        self._fusion = None
        self._last_scan = None
        self._execution_log = []

    # ==================== LAZY LOADING ====================

    @property
    def hft(self):
        """Unlimited HFT for execution - 63 wallets, 15K orders/sec."""
        if not self._hft:
            from executor.unlimited_hft import get_unlimited_hft
            self._hft = get_unlimited_hft()
            self._hft.activate()
        return self._hft

    @property
    def lightning(self):
        """Lightning rod for Cloudflare-aware connections."""
        if not hasattr(self, '_lightning') or self._lightning is None:
            from executor.polymarket_lightning import get_lightning
            self._lightning = get_lightning()
        return self._lightning

    @property
    def wisdom(self):
        """Yair Wisdom Engine for opportunity detection."""
        if not self._wisdom:
            try:
                from autonomous.yair_wisdom_engine import get_wisdom
                self._wisdom = get_wisdom()
            except:
                self._wisdom = None
        return self._wisdom

    @property
    def fusion(self):
        """Knowledge Fusion for context."""
        if not self._fusion:
            try:
                from autonomous.knowledge_fusion import get_fusion
                self._fusion = get_fusion()
            except:
                self._fusion = None
        return self._fusion

    # ==================== STATUS ====================

    def status(self) -> Dict:
        """Get bridge status using unlimited HFT."""
        # Get unlimited HFT status (63 wallets)
        hft_status = self.hft.status()

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hft_ready": hft_status.get("wallets_active", 0) > 0,
            "hft_wallets": hft_status.get("wallets_total", 0),
            "hft_active": hft_status.get("wallets_active", 0),
            "hft_capacity": hft_status.get("theoretical_capacity", "0/sec"),
            "hft_mode": hft_status.get("mode", "LIMITED"),
            "wisdom_loaded": self.wisdom is not None,
            "fusion_loaded": self.fusion is not None,
            "executions_today": len(self._execution_log),
            "last_scan": self._last_scan
        }

    # ==================== OPPORTUNITY DETECTION ====================

    def scan_opportunities(self) -> List[ExecutionOpportunity]:
        """
        Scan for all types of opportunities.

        Sources:
        1. Yair Wisdom Engine - merge arb, ESPN signals
        2. Market scanning - thin books, grids
        3. Knowledge Fusion - strategic insights
        """
        opportunities = []
        self._last_scan = datetime.now(timezone.utc).isoformat()

        # 1. Check Yair Wisdom signals
        if self.wisdom:
            wisdom_opps = self._scan_wisdom_opportunities()
            opportunities.extend(wisdom_opps)

        # 2. Scan for merge arbitrage (YES + NO < $0.98)
        merge_opps = self._scan_merge_arbitrage()
        opportunities.extend(merge_opps)

        # 3. Check knowledge fusion for strategic opportunities
        if self.fusion:
            fusion_opps = self._scan_fusion_opportunities()
            opportunities.extend(fusion_opps)

        return opportunities

    def _scan_wisdom_opportunities(self) -> List[ExecutionOpportunity]:
        """Scan Yair Wisdom Engine for opportunities."""
        opportunities = []

        # Check for active wisdom signals
        if hasattr(self.wisdom, 'get_active_signals'):
            signals = self.wisdom.get_active_signals()
            for signal in signals:
                opp = ExecutionOpportunity(
                    opportunity_type=signal.get("type", "wisdom"),
                    token_id=signal.get("token_id", ""),
                    side=signal.get("side", "BUY"),
                    price=signal.get("price", 0.5),
                    size=signal.get("size", 10),
                    confidence=signal.get("confidence", 0.7),
                    source="yair_wisdom",
                    reason=signal.get("reason", "Wisdom signal")
                )
                if opp.token_id:
                    opportunities.append(opp)

        return opportunities

    def _scan_merge_arbitrage(self) -> List[ExecutionOpportunity]:
        """Scan for merge arbitrage opportunities (YES + NO < $0.98)."""
        opportunities = []

        try:
            import requests

            # Query active markets via gamma API
            response = requests.get(
                "https://gamma-api.polymarket.com/markets?closed=false&limit=50",
                timeout=10,
                headers={"User-Agent": "Mozilla/5.0 (compatible; HFT-Bot/1.0)"}
            )

            if response.status_code == 200:
                markets = response.json()

                for market in markets:
                    # Gamma API uses outcomePrices and clobTokenIds (not tokens)
                    prices = market.get("outcomePrices", [])
                    token_ids = market.get("clobTokenIds", [])

                    if len(prices) >= 2 and len(token_ids) >= 2:
                        try:
                            # First price is YES, second is NO
                            yes_price = float(prices[0])
                            no_price = float(prices[1])
                            yes_token = token_ids[0]
                            no_token = token_ids[1]

                            total = yes_price + no_price

                            # Check for merge arb: YES + NO < 0.98
                            if total < 0.98:
                                arb_profit = 1.0 - total

                                opp = ExecutionOpportunity(
                                    opportunity_type="merge_arb",
                                    token_id=yes_token,
                                    side="BOTH",
                                    price=yes_price,
                                    size=min(100, 10 / arb_profit) if arb_profit > 0 else 10,
                                    confidence=0.95,
                                    source="merge_scan",
                                    reason=f"Merge arb: YES={yes_price:.3f} + NO={no_price:.3f} = {total:.3f} (profit: ${arb_profit:.3f}/share)"
                                )
                                opportunities.append(opp)
                        except (ValueError, IndexError):
                            continue

        except Exception as e:
            pass  # Silent fail for scan

        return opportunities

    def _scan_fusion_opportunities(self) -> List[ExecutionOpportunity]:
        """Get opportunities from knowledge fusion insights."""
        opportunities = []

        if self.fusion:
            try:
                # Get trading fusion insight
                trading_insight = self.fusion.fuse_for_decision("trading")
                if trading_insight and trading_insight.confidence > 0.8:
                    # High confidence trading insight available
                    # This provides context for execution, not specific trades
                    pass
            except:
                pass

        return opportunities

    # ==================== EXECUTION ====================

    def execute_opportunity(self, opp: ExecutionOpportunity) -> ExecutionResult:
        """
        Execute a single opportunity via HFT.

        Routes to appropriate execution method based on type.
        """
        try:
            if opp.opportunity_type == "merge_arb":
                return self._execute_merge_arb(opp)
            elif opp.opportunity_type == "grid_capture":
                return self._execute_grid(opp)
            else:
                return self._execute_single(opp)

        except Exception as e:
            return ExecutionResult(
                success=False,
                opportunity=opp,
                orders_placed=0,
                latency_ms=0,
                error=str(e)
            )

    def _execute_single(self, opp: ExecutionOpportunity) -> ExecutionResult:
        """Execute single order."""
        import time
        start = time.time()

        result = self.hft.place_order(
            token_id=opp.token_id,
            price=opp.price,
            size=opp.size,
            side=opp.side
        )

        elapsed_ms = (time.time() - start) * 1000

        return ExecutionResult(
            success=result.get("success", False),
            opportunity=opp,
            orders_placed=1 if result.get("success") else 0,
            latency_ms=elapsed_ms
        )

    def _execute_grid(self, opp: ExecutionOpportunity) -> ExecutionResult:
        """Execute grid of orders."""
        import time
        start = time.time()

        result = self.hft.place_grid(
            token_id=opp.token_id,
            center_price=opp.price,
            spread_bps=100,
            levels=5,
            size=opp.size
        )

        elapsed_ms = (time.time() - start) * 1000

        return ExecutionResult(
            success=result.get("success", False),
            opportunity=opp,
            orders_placed=result.get("orders_placed", 0),
            latency_ms=elapsed_ms
        )

    def _execute_merge_arb(self, opp: ExecutionOpportunity) -> ExecutionResult:
        """
        Execute merge arbitrage.

        Buy YES at bid, buy NO at bid, merge for $1.
        """
        import time
        start = time.time()

        # For merge arb, place limit orders on YES side
        # The full merge execution would need to also buy NO
        result = self.hft.place_order(
            token_id=opp.token_id,
            price=opp.price,
            size=opp.size,
            side="BUY"
        )

        elapsed_ms = (time.time() - start) * 1000

        return ExecutionResult(
            success=result.get("success", False),
            opportunity=opp,
            orders_placed=1 if result.get("success") else 0,
            latency_ms=elapsed_ms,
            error=None if result.get("success") else "Merge arb partial (YES only)"
        )

    # ==================== MAIN CYCLE ====================

    def scan_and_execute(self, dry_run: bool = False) -> Dict:
        """
        Full cycle: scan for opportunities and execute.

        Args:
            dry_run: If True, scan but don't execute

        Returns:
            Summary of scan and execution results
        """
        # Scan
        opportunities = self.scan_opportunities()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "opportunities_found": len(opportunities),
            "opportunities": [
                {
                    "type": o.opportunity_type,
                    "token": o.token_id[:20] + "..." if len(o.token_id) > 20 else o.token_id,
                    "confidence": o.confidence,
                    "reason": o.reason
                }
                for o in opportunities
            ],
            "dry_run": dry_run,
            "executions": []
        }

        if dry_run or not opportunities:
            return results

        # Execute high-confidence opportunities
        for opp in opportunities:
            if opp.confidence >= 0.7:  # Only execute high confidence
                exec_result = self.execute_opportunity(opp)
                self._execution_log.append({
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "opportunity": opp.opportunity_type,
                    "success": exec_result.success,
                    "orders": exec_result.orders_placed
                })
                results["executions"].append({
                    "type": opp.opportunity_type,
                    "success": exec_result.success,
                    "orders_placed": exec_result.orders_placed,
                    "latency_ms": exec_result.latency_ms
                })

        return results

    def run_hft_cycle(self) -> Dict:
        """
        Run one HFT cycle - for use in backend_loop.

        Returns status and any execution results.
        """
        status = self.status()

        # Only scan/execute if HFT is ready
        if not status.get("hft_ready"):
            return {
                "success": False,
                "status": status,
                "error": "HFT not ready (no active wallets)"
            }

        # Scan and execute
        scan_results = self.scan_and_execute(dry_run=False)

        return {
            "success": True,
            "status": status,
            "scan": scan_results,
            "hft_capacity": status.get("hft_capacity", 0),
            "executions": len(scan_results.get("executions", []))
        }

    def save_state(self):
        """Save bridge state to file."""
        state = {
            "last_scan": self._last_scan,
            "execution_log": self._execution_log[-100:],  # Keep last 100
            "saved_at": datetime.now(timezone.utc).isoformat()
        }

        state_file = STATE_DIR / "hft_bridge.json"
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)


# Singleton instance
_bridge = None

def get_bridge() -> HFTExecutionBridge:
    """Get or create HFT Execution Bridge singleton."""
    global _bridge
    if _bridge is None:
        _bridge = HFTExecutionBridge()
    return _bridge


# Convenience alias
hft_bridge = get_bridge()


if __name__ == "__main__":
    # Test the bridge
    bridge = get_bridge()

    print("=" * 60)
    print("HFT EXECUTION BRIDGE")
    print("=" * 60)

    # Status
    print("\n[STATUS]")
    status = bridge.status()
    print(f"  HFT Ready: {status['hft_ready']}")
    print(f"  Wallets: {status['hft_wallets']}")
    print(f"  Capacity: {status['hft_capacity']}")
    print(f"  Wisdom Loaded: {status['wisdom_loaded']}")
    print(f"  Fusion Loaded: {status['fusion_loaded']}")

    # Scan (dry run)
    print("\n[SCANNING FOR OPPORTUNITIES]")
    results = bridge.scan_and_execute(dry_run=True)
    print(f"  Found: {results['opportunities_found']} opportunities")
    for opp in results['opportunities'][:5]:
        print(f"    - {opp['type']}: {opp['reason'][:50]}...")

    print("\n" + "=" * 60)
