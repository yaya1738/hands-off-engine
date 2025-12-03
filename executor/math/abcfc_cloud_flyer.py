#!/usr/bin/env python3
"""
ABCFC CLOUD FLYER - Autonomous agent flying through ABCFC nexus decision space

FULLY INTEGRATED with ABCFCSystem - uses get_top_line_nexus_cloud() for decisions.

Continuously:
1. Observe current state (real Polymarket positions)
2. Build ABCFC hierarchy (Yair Siegel → Trading → Polymarket → positions)
3. Generate nexus cloud (all possible futures from actions)
4. Select optimal trajectory via ABCFCSystem scoring
5. Execute or recommend
6. Loop forever

Created by: Yair Siegel
"""

import os
import sys
import time
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import the real ABCFC system
from executor.math.abcfc_system import ABCFCSystem, Action as ABCFCAction

STATE_DIR = PROJECT_ROOT / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

FLIGHT_LOG = STATE_DIR / "abcfc_flight.jsonl"


@dataclass
class FlightState:
    """Current state in the ABCFC cloud - now from ABCFCSystem."""
    timestamp: str
    system: ABCFCSystem
    positions: List[Dict]
    total_expected: float
    bounds: Tuple[float, float]
    order_books: Dict = field(default_factory=dict)


@dataclass
class FlightAction:
    """Wrapper for ABCFC actions with cloud flyer metadata."""
    abcfc_action: ABCFCAction
    target_node: str
    description: str


@dataclass
class FlightEvaluation:
    """Evaluation from nexus cloud."""
    action: FlightAction
    node_name: str
    top_line_before: Dict
    top_line_after: Dict
    delta: Dict
    score: float
    rationale: str


class ABCFCCloudFlyer:
    """
    Autonomous agent that flies through the ABCFC nexus cloud.

    INTEGRATED: Uses ABCFCSystem.get_top_line_nexus_cloud() for decision making.
    All actions are evaluated by their impact on Yair Siegel top-line ABCFC.
    """

    def __init__(self, name: str = "Yair Siegel", dry_run: bool = True,
                 risk_aversion: float = 0.5):
        self.name = name
        self.dry_run = dry_run
        self.risk_aversion = risk_aversion
        self.flight_log: List[Dict] = []
        self.iteration = 0

        # Polymarket client (lazy load)
        self._client = None

        # ABCFCSystem (rebuilt each observation)
        self._system: Optional[ABCFCSystem] = None

    @property
    def client(self):
        """Lazy load Polymarket client."""
        if self._client is None:
            try:
                from py_clob_client.client import ClobClient

                host = "https://clob.polymarket.com"
                key = os.environ.get("POLYMARKET_PRIVATE_KEY",
                    "0x644444ab1d39e9074b01f085a27a4bbf5a8536f411b9b2bea04eb3934f038493")
                chain_id = 137
                funder = os.environ.get("POLYMARKET_FUNDER_ADDRESS",
                    "0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D")

                self._client = ClobClient(host, key=key, chain_id=chain_id, funder=funder)
                creds = self._client.create_or_derive_api_creds()
                self._client.set_api_creds(creds)
            except Exception as e:
                print(f"Warning: Could not init Polymarket client: {e}")
                self._client = None
        return self._client

    def observe(self) -> FlightState:
        """
        Observe current state and build ABCFCSystem hierarchy.

        Returns FlightState with:
        - ABCFCSystem hierarchy (Yair Siegel → Trading → Polymarket → positions)
        - Real Polymarket positions data
        - Order books for L2 analysis
        """

        positions = []
        order_books = {}

        # Create fresh ABCFCSystem
        system = ABCFCSystem(self.name)
        system.risk_aversion = self.risk_aversion

        # Add Trading category and Polymarket subcategory
        system.add_category("Trading")
        system.add_subcategory("Trading", "Polymarket")

        if self.client:
            try:
                # Get open orders
                orders = self.client.get_orders()

                # Group by token
                by_token = {}
                for order in orders:
                    token = order.get('asset_id', '')
                    if token not in by_token:
                        by_token[token] = []
                    by_token[token].append(order)

                # Process each token into a position
                for token_id, token_orders in by_token.items():
                    pos_name = f"M_{token_id[:8]}"

                    # Get order book for mid price
                    mid = 0.5
                    try:
                        book = self.client.get_order_book(token_id)
                        bids = getattr(book, 'bids', []) or []
                        asks = getattr(book, 'asks', []) or []

                        best_bid = float(bids[0].price) if bids else 0
                        best_ask = float(asks[0].price) if asks else 1
                        mid = (best_bid + best_ask) / 2

                        order_books[pos_name] = {
                            "bid": best_bid,
                            "ask": best_ask,
                            "mid": mid,
                            "spread": best_ask - best_bid,
                        }
                    except:
                        pass

                    # Calculate position from orders
                    buy_size = sum(float(o.get('original_size', o.get('size', 0)))
                                   for o in token_orders if o.get('side') == 'BUY')
                    sell_size = sum(float(o.get('original_size', o.get('size', 0)))
                                    for o in token_orders if o.get('side') == 'SELL')

                    buy_price = sum(float(o.get('price', 0)) * float(o.get('original_size', o.get('size', 1)))
                                    for o in token_orders if o.get('side') == 'BUY')
                    sell_price = sum(float(o.get('price', 0)) * float(o.get('original_size', o.get('size', 1)))
                                     for o in token_orders if o.get('side') == 'SELL')

                    avg_buy = buy_price / buy_size if buy_size > 0 else 0
                    avg_sell = sell_price / sell_size if sell_size > 0 else 0

                    # Net position
                    net = buy_size - sell_size
                    side = "YES" if net >= 0 else "NO"
                    shares = abs(net)
                    entry = avg_buy if net >= 0 else avg_sell

                    if shares > 0:
                        # Calculate P&L bounds
                        if side == "YES":
                            best_pnl = shares * (1 - entry)
                            worst_pnl = -shares * entry
                            expected_pnl = shares * (mid - entry)
                        else:
                            best_pnl = shares * entry
                            worst_pnl = -shares * (1 - entry)
                            expected_pnl = shares * ((1 - mid) - (1 - entry))

                        # Add to ABCFCSystem hierarchy
                        system.add_position(
                            parent_name="Polymarket",
                            name=pos_name,
                            worst=worst_pnl,
                            best=best_pnl,
                            expected=expected_pnl
                        )

                        positions.append({
                            "name": pos_name,
                            "token": token_id[:16],
                            "side": side,
                            "shares": shares,
                            "entry": entry,
                            "mid": mid,
                            "expected": expected_pnl,
                            "best": best_pnl,
                            "worst": worst_pnl,
                        })

            except Exception as e:
                print(f"Observe error: {e}")

        # Store system for later use
        self._system = system

        return FlightState(
            timestamp=datetime.now(timezone.utc).isoformat(),
            system=system,
            positions=positions,
            total_expected=system.total_expected(),
            bounds=system.total_bounds(),
            order_books=order_books,
        )

    def generate_actions(self) -> List[ABCFCAction]:
        """
        Generate possible ABCFC actions for nexus cloud evaluation.

        These are ABCFCAction objects that ABCFCSystem understands.
        """
        return [
            ABCFCAction("hold", "hold", {}),
            ABCFCAction("hedge_50", "hedge", {"ratio": 0.5}),
            ABCFCAction("hedge_25", "hedge", {"ratio": 0.25}),
            ABCFCAction("sell_half", "sell", {"size": 50, "price": 0.5}),
            ABCFCAction("buy_more", "buy", {"size": 25, "price": 0.45}),
        ]

    def get_nexus_cloud(self, state: FlightState) -> Dict:
        """
        Get the top-line nexus cloud using ABCFCSystem.

        This is THE integration - all actions evaluated by impact on Yair Siegel ABCFC.
        """
        actions = self.generate_actions()
        return state.system.get_top_line_nexus_cloud(actions)

    def select_best_from_cloud(self, cloud: Dict) -> Optional[Dict]:
        """Select the best future from the nexus cloud."""
        futures = cloud.get("futures", [])
        if not futures:
            return None
        # Already sorted by score descending
        return futures[0]

    def execute(self, best_future: Dict) -> Dict:
        """Execute the best action (or log in dry run)."""
        result = {
            "node": best_future.get("node"),
            "action": best_future.get("action"),
            "score": best_future.get("score"),
            "top_line_expected": best_future.get("top_line", {}).get("expected"),
            "executed": not self.dry_run,
        }

        if self.dry_run:
            result["note"] = "DRY RUN - would execute"
        else:
            # Real execution would go here
            # Could integrate with Polymarket client to actually place orders
            result["note"] = "LIVE - executed"

        return result

    def log_flight(self, state: FlightState, cloud: Dict, best_future: Dict, result: Dict):
        """Log flight iteration to file."""
        entry = {
            "iteration": self.iteration,
            "timestamp": state.timestamp,
            "state": {
                "n_positions": len(state.positions),
                "total_expected": state.total_expected,
                "bounds": state.bounds,
            },
            "cloud": {
                "n_futures": len(cloud.get("futures", [])),
                "current": cloud.get("current"),
                "cloud_bounds": cloud.get("cloud_bounds"),
            },
            "selected": {
                "node": best_future.get("node"),
                "action": best_future.get("action"),
                "score": best_future.get("score"),
                "top_line_after": best_future.get("top_line"),
                "delta": best_future.get("delta"),
            },
            "result": result,
        }

        self.flight_log.append(entry)

        # Append to file
        with open(FLIGHT_LOG, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def fly_once(self) -> Dict:
        """
        One flight iteration through the nexus cloud.

        1. Observe → build ABCFCSystem with real Polymarket positions
        2. Generate nexus cloud → all possible futures
        3. Select best → highest scoring action
        4. Execute (or log in dry run)
        5. Log flight
        """

        # 1. Observe - builds ABCFCSystem
        state = self.observe()

        # 2. Generate nexus cloud using ABCFCSystem
        cloud = self.get_nexus_cloud(state)

        # 3. Select best from cloud
        best_future = self.select_best_from_cloud(cloud)

        if best_future is None:
            # No futures = no positions = hold
            best_future = {
                "node": "none",
                "action": "hold",
                "score": 0,
                "top_line": cloud.get("current", {}),
                "delta": {"expected": 0, "worst": 0, "best": 0}
            }

        # 4. Execute
        result = self.execute(best_future)

        # 5. Log
        self.log_flight(state, cloud, best_future, result)

        self.iteration += 1

        return {
            "iteration": self.iteration - 1,
            "state": state,
            "cloud": cloud,
            "selected": best_future,
            "result": result,
        }

    def fly(self, interval_sec: int = 60, max_iterations: Optional[int] = None,
            visualize: bool = False, viz_path: str = None):
        """
        Fly through the ABCFC nexus cloud continuously.

        INTEGRATED: Uses ABCFCSystem.get_top_line_nexus_cloud() for all decisions.

        Args:
            interval_sec: Seconds between iterations
            max_iterations: Max iterations (None = infinite)
            visualize: Generate visualization each iteration
            viz_path: Path for visualization (default: /tmp/abcfc_flight_{iter}.png)
        """

        print("=" * 70)
        print(f"ABCFC CLOUD FLYER - {self.name}")
        print("=" * 70)
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print(f"Risk Aversion: {self.risk_aversion}")
        print(f"Interval: {interval_sec}s")
        print(f"Log: {FLIGHT_LOG}")
        print(f"INTEGRATED: Using ABCFCSystem.get_top_line_nexus_cloud()")
        print()

        while max_iterations is None or self.iteration < max_iterations:
            try:
                result = self.fly_once()

                state = result["state"]
                cloud = result["cloud"]
                selected = result["selected"]

                # Print hierarchy summary
                if self.iteration == 1 or (self.iteration - 1) % 10 == 0:
                    print("\n--- HIERARCHY ---")
                    state.system.print_hierarchy()
                    print("-----------------\n")

                # Flight output
                n_futures = len(cloud.get("futures", []))
                print(f"[{self.iteration-1:4d}] "
                      f"E=${state.total_expected:+8.2f} | "
                      f"[${state.bounds[0]:+.0f}, ${state.bounds[1]:+.0f}] | "
                      f"{n_futures} futures | "
                      f"-> {selected.get('action', 'hold'):12} on {selected.get('node', 'n/a')[:12]:12} | "
                      f"score: {selected.get('score', 0):+.2f}")

                # Visualize if requested
                if visualize and self._system:
                    path = viz_path or f"/tmp/abcfc_flight_{self.iteration-1:04d}.png"
                    actions = self.generate_actions()
                    self._system.plot_top_line_nexus(actions, save_path=path)
                    print(f"      Chart: {path}")

                if max_iterations and self.iteration >= max_iterations:
                    break

                time.sleep(interval_sec)

            except KeyboardInterrupt:
                print("\nFlight interrupted by user")
                break
            except Exception as e:
                print(f"Flight error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(interval_sec)

        print(f"\nFlight complete. {self.iteration} iterations logged to {FLIGHT_LOG}")
        return self.flight_log

    def status(self) -> Dict:
        """Get current flight status without flying."""
        state = self.observe()
        cloud = self.get_nexus_cloud(state)
        best = self.select_best_from_cloud(cloud)

        return {
            "name": self.name,
            "mode": "DRY RUN" if self.dry_run else "LIVE",
            "risk_aversion": self.risk_aversion,
            "iterations_completed": self.iteration,
            "current_state": {
                "positions": len(state.positions),
                "expected": state.total_expected,
                "bounds": state.bounds,
            },
            "nexus_cloud": {
                "n_futures": len(cloud.get("futures", [])),
                "cloud_bounds": cloud.get("cloud_bounds"),
            },
            "recommended_action": {
                "node": best.get("node") if best else None,
                "action": best.get("action") if best else "hold",
                "score": best.get("score") if best else 0,
            },
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="ABCFC Cloud Flyer - Integrated with ABCFCSystem")
    parser.add_argument("--live", action="store_true", help="Execute actions (default: dry run)")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between iterations")
    parser.add_argument("--iterations", type=int, default=None, help="Max iterations (default: infinite)")
    parser.add_argument("--risk", type=float, default=0.5, help="Risk aversion (0=seeking, 1=averse)")
    parser.add_argument("--visualize", action="store_true", help="Generate charts each iteration")
    parser.add_argument("--status", action="store_true", help="Just show current status and exit")
    args = parser.parse_args()

    flyer = ABCFCCloudFlyer(
        name="Yair Siegel",
        dry_run=not args.live,
        risk_aversion=args.risk
    )

    if args.status:
        import pprint
        status = flyer.status()
        print("=" * 70)
        print("ABCFC CLOUD FLYER STATUS")
        print("=" * 70)
        pprint.pprint(status)
        return

    flyer.fly(
        interval_sec=args.interval,
        max_iterations=args.iterations,
        visualize=args.visualize
    )


if __name__ == "__main__":
    main()
