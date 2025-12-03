#!/usr/bin/env python3
"""
Sharp Wallet Tracker - Follow Smart Money
Implementation of Yair's teaching: 'The blockchain never forgets -
every wallet has permanent track record.'

YAIR'S TEACHINGS ON WALLETS:
- Build database of sharp vs dumb wallets
- Follow wallets with proven edge
- Fade wallets that consistently lose
- Track smart money rotation into new categories

Serving: Yair Siegel
"""

import json
import os
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"
SHARP_WALLETS_FILE = STATE_DIR / "sharp_wallets.json"
WALLET_HISTORY_LOG = STATE_DIR / "wallet_tracking.jsonl"

# Known sharp wallets from Yair's memory / leaderboards
# These are public Polymarket addresses
SEED_SHARP_WALLETS = [
    # Top leaderboard traders (public info)
    # Format: {"address": "0x...", "known_as": "nickname", "edge_category": "category"}
]


class SharpWalletTracker:
    """Track and learn from sharp (profitable) wallets."""

    def __init__(self):
        self.state = self._load_state()
        self.api_base = "https://gamma-api.polymarket.com"

    def _load_state(self) -> Dict:
        if SHARP_WALLETS_FILE.exists():
            with open(SHARP_WALLETS_FILE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "wallets": {},  # address -> wallet data
            "sharp_list": [],  # addresses of confirmed sharps
            "fade_list": [],  # addresses to fade (consistently wrong)
            "last_leaderboard_check": None,
            "follow_signals": []
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(SHARP_WALLETS_FILE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_tracking(self, event: Dict):
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        event["master"] = MASTER
        with open(WALLET_HISTORY_LOG, 'a') as f:
            f.write(json.dumps(event) + "\n")

    def fetch_leaderboard(self) -> List[Dict]:
        """
        Yair's teaching: 'Leaderboards exist on Polymarket (starting point)'
        Fetch top traders from leaderboard.
        """
        try:
            # Polymarket profiles API
            response = requests.get(
                f"{self.api_base}/profiles",
                params={"limit": 50, "sort": "volume", "order": "desc"},
                timeout=15
            )

            if response.status_code == 200:
                profiles = response.json()
                return profiles

            # Alternative: Try to get from activity
            response = requests.get(
                f"{self.api_base}/activity",
                params={"limit": 100},
                timeout=15
            )

            if response.status_code == 200:
                activity = response.json()
                # Extract unique traders
                traders = {}
                for trade in activity:
                    addr = trade.get("user") or trade.get("maker") or trade.get("taker")
                    if addr and addr not in traders:
                        traders[addr] = {
                            "address": addr,
                            "sample_trade": trade
                        }
                return list(traders.values())[:50]

        except Exception as e:
            print(f"Error fetching leaderboard: {e}")

        return []

    def analyze_wallet(self, address: str) -> Dict:
        """
        Yair's teaching: 'All past trades, all markets, all outcomes.
        Win rate trackable per wallet. Edge measurable over time.'
        """
        analysis = {
            "address": address,
            "analyzed_at": datetime.now(timezone.utc).isoformat(),
            "trades_found": 0,
            "estimated_pnl": 0.0,
            "win_rate": 0.0,
            "categories": {},
            "is_sharp": False,
            "confidence": 0.0
        }

        try:
            # Get wallet's trading activity
            response = requests.get(
                f"{self.api_base}/activity",
                params={"user": address, "limit": 100},
                timeout=15
            )

            if response.status_code != 200:
                return analysis

            trades = response.json()
            analysis["trades_found"] = len(trades)

            if not trades:
                return analysis

            # Analyze trades
            wins = 0
            losses = 0
            by_category = defaultdict(lambda: {"trades": 0, "wins": 0})

            for trade in trades:
                outcome = trade.get("outcome")
                side = trade.get("side", "").upper()
                market = trade.get("market", "")

                # Categorize
                category = self._categorize_market(market)
                by_category[category]["trades"] += 1

                # Track win/loss (simplified - would need resolution data)
                if outcome and outcome.get("resolved"):
                    if outcome.get("winner") == side:
                        wins += 1
                        by_category[category]["wins"] += 1
                    else:
                        losses += 1

            total_resolved = wins + losses
            if total_resolved > 0:
                analysis["win_rate"] = wins / total_resolved
                analysis["is_sharp"] = analysis["win_rate"] > 0.55  # >55% = sharp

            analysis["categories"] = dict(by_category)

            # Confidence in assessment
            if total_resolved >= 50:
                analysis["confidence"] = 0.8
            elif total_resolved >= 20:
                analysis["confidence"] = 0.6
            elif total_resolved >= 10:
                analysis["confidence"] = 0.4
            else:
                analysis["confidence"] = 0.2

        except Exception as e:
            print(f"Error analyzing wallet {address[:10]}...: {e}")

        return analysis

    def _categorize_market(self, market_name: str) -> str:
        """Categorize market for category-specific edge tracking."""
        m = market_name.lower()

        if any(kw in m for kw in ['nba', 'nfl', 'mlb', 'game', 'win', 'playoff']):
            return "sports"
        elif any(kw in m for kw in ['trump', 'biden', 'election', 'president']):
            return "politics"
        elif any(kw in m for kw in ['ukraine', 'russia', 'war', 'military']):
            return "war"
        elif any(kw in m for kw in ['bitcoin', 'btc', 'eth', 'crypto']):
            return "crypto"
        elif any(kw in m for kw in ['fed', 'rate', 'inflation', 'gdp']):
            return "macro"
        else:
            return "other"

    def update_sharp_list(self) -> Dict:
        """
        Scan and update list of sharp wallets.
        """
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "wallets_checked": 0,
            "new_sharps": [],
            "new_fades": []
        }

        # Get leaderboard
        leaderboard = self.fetch_leaderboard()
        results["wallets_checked"] = len(leaderboard)

        for profile in leaderboard[:20]:  # Top 20
            addr = profile.get("address") or profile.get("user")
            if not addr:
                continue

            # Analyze if not recently analyzed
            existing = self.state["wallets"].get(addr, {})
            last_check = existing.get("analyzed_at", "")

            # Re-check if older than 24 hours
            should_analyze = True
            if last_check:
                try:
                    last_dt = datetime.fromisoformat(last_check.replace("Z", "+00:00"))
                    if datetime.now(timezone.utc) - last_dt < timedelta(hours=24):
                        should_analyze = False
                except:
                    pass

            if should_analyze:
                analysis = self.analyze_wallet(addr)
                self.state["wallets"][addr] = analysis

                # Update sharp/fade lists
                if analysis["is_sharp"] and analysis["confidence"] >= 0.5:
                    if addr not in self.state["sharp_list"]:
                        self.state["sharp_list"].append(addr)
                        results["new_sharps"].append(addr[:10] + "...")
                elif analysis["win_rate"] < 0.45 and analysis["confidence"] >= 0.5:
                    if addr not in self.state["fade_list"]:
                        self.state["fade_list"].append(addr)
                        results["new_fades"].append(addr[:10] + "...")

        self.state["last_leaderboard_check"] = results["timestamp"]
        self._save_state()

        return results

    def get_sharp_positions(self, market_id: str = None) -> List[Dict]:
        """
        Yair's teaching: 'See who's positioned where.
        Verify if sharp bettors with me or against me.'
        """
        positions = []

        try:
            # Get activity for market
            params = {"limit": 100}
            if market_id:
                params["market"] = market_id

            response = requests.get(
                f"{self.api_base}/activity",
                params=params,
                timeout=15
            )

            if response.status_code != 200:
                return positions

            activity = response.json()

            # Filter for sharp wallets
            for trade in activity:
                trader = trade.get("user") or trade.get("maker")
                if trader in self.state["sharp_list"]:
                    positions.append({
                        "sharp_wallet": trader[:10] + "...",
                        "side": trade.get("side"),
                        "size": trade.get("size"),
                        "price": trade.get("price"),
                        "market": trade.get("market", "")[:40],
                        "time": trade.get("timestamp")
                    })

        except Exception as e:
            print(f"Error getting sharp positions: {e}")

        return positions

    def generate_follow_signals(self) -> List[Dict]:
        """
        Yair's teaching: 'Follow wallets with proven edge.'
        Generate signals based on sharp wallet activity.
        """
        signals = []

        try:
            # Get recent activity
            response = requests.get(
                f"{self.api_base}/activity",
                params={"limit": 200},
                timeout=15
            )

            if response.status_code != 200:
                return signals

            activity = response.json()

            # Track sharp wallet actions
            sharp_activity = defaultdict(lambda: {"YES": 0, "NO": 0})

            for trade in activity:
                trader = trade.get("user") or trade.get("maker")
                if trader in self.state["sharp_list"]:
                    market = trade.get("market", "")
                    side = trade.get("side", "").upper()
                    size = float(trade.get("size", 0))

                    if side in ["YES", "NO"]:
                        sharp_activity[market][side] += size

            # Generate signals where sharps are concentrated
            for market, sides in sharp_activity.items():
                total = sides["YES"] + sides["NO"]
                if total > 0:
                    yes_pct = sides["YES"] / total
                    no_pct = sides["NO"] / total

                    # Strong signal if sharps concentrated on one side
                    if yes_pct > 0.7:
                        signals.append({
                            "market": market[:50],
                            "signal": "FOLLOW_YES",
                            "sharp_bias": yes_pct,
                            "sharp_volume": sides["YES"],
                            "teaching": "Follow wallets with proven edge"
                        })
                    elif no_pct > 0.7:
                        signals.append({
                            "market": market[:50],
                            "signal": "FOLLOW_NO",
                            "sharp_bias": no_pct,
                            "sharp_volume": sides["NO"],
                            "teaching": "Follow wallets with proven edge"
                        })

        except Exception as e:
            print(f"Error generating follow signals: {e}")

        self.state["follow_signals"] = signals[:10]
        self._save_state()

        return signals

    def run_tracking_cycle(self) -> Dict:
        """Run full sharp wallet tracking cycle."""
        print("=" * 70)
        print("SHARP WALLET TRACKER")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[YAIR'S TEACHING]")
        print("  'The blockchain never forgets - every wallet has permanent track record.'")
        print("  'Follow wallets with proven edge. Fade wallets that consistently lose.'")
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Update sharp list
        print("[UPDATING SHARP LIST]")
        update = self.update_sharp_list()
        results["update"] = update
        print(f"  Wallets checked: {update['wallets_checked']}")
        print(f"  New sharps found: {len(update['new_sharps'])}")
        print(f"  New fades found: {len(update['new_fades'])}")
        print()

        # Current lists
        print("[SHARP WALLET DATABASE]")
        print(f"  Confirmed sharps: {len(self.state['sharp_list'])}")
        print(f"  Confirmed fades: {len(self.state['fade_list'])}")
        print(f"  Total tracked: {len(self.state['wallets'])}")
        print()

        # Generate follow signals
        print("[FOLLOW SIGNALS]")
        signals = self.generate_follow_signals()
        results["signals"] = signals
        print(f"  Signals generated: {len(signals)}")
        for sig in signals[:5]:
            print(f"    - {sig['signal']}: {sig['market'][:35]}...")
            print(f"      Sharp bias: {sig['sharp_bias']:.0%}")
        print()

        # Summary
        print("=" * 70)
        print("TRACKING SUMMARY")
        print("=" * 70)
        print(f"  Sharp wallets: {len(self.state['sharp_list'])}")
        print(f"  Fade wallets: {len(self.state['fade_list'])}")
        print(f"  Active signals: {len(signals)}")
        print()

        if signals:
            print("ACTIONABLE (from Yair's teaching 'follow sharps'):")
            for sig in signals[:3]:
                print(f"  {sig['signal']}: {sig['market'][:40]}")

        self._log_tracking({
            "type": "tracking_cycle",
            "sharps": len(self.state["sharp_list"]),
            "fades": len(self.state["fade_list"]),
            "signals": len(signals)
        })

        return results


def main():
    tracker = SharpWalletTracker()
    return tracker.run_tracking_cycle()


if __name__ == "__main__":
    main()
