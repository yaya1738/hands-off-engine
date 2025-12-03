#!/usr/bin/env python3
"""
Glitch Detector - Safety System
Implementation of Yair's critical teaching on glitches.

YAIR'S TEACHING ON GLITCHES:
- 'Polymarket Can Glitch - UI glitches, feed glitches, API connector issues'
- 'Don't trust single data point'
- 'Validate before acting'
- 'Sanity checks on prices'
- 'Don't execute on glitched data'
- 'Fail safe > fail fast'

WATCH FOR:
- Stale prices
- Impossible spreads
- Missing data
- Timeout errors
- Weird order book states

Serving: Yair Siegel
"""

import json
import os
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"

MASTER = "Yair Siegel"
GLITCH_STATE = STATE_DIR / "glitch_detection.json"
GLITCH_LOG = STATE_DIR / "glitch_alerts.jsonl"

# Sanity bounds from Yair's teaching
SANITY_BOUNDS = {
    "max_spread": 0.20,           # Spread > 20% is suspicious
    "min_price": 0.001,           # Below 0.1% is edge case
    "max_price": 0.999,           # Above 99.9% is edge case
    "max_price_change_1m": 0.10,  # >10% move in 1 minute is suspicious
    "max_price_change_5m": 0.20,  # >20% move in 5 minutes is suspicious
    "min_liquidity": 100,         # Below $100 liquidity is thin
    "stale_threshold_seconds": 300  # Price older than 5 min is stale
}


class GlitchDetector:
    """
    Detect glitches before they cause losses.

    Yair's teaching: 'The Risk - Glitch shows wrong price →
    Bot executes on bad data → Real loss from fake signal'
    """

    def __init__(self):
        self.state = self._load_state()
        self.price_history = {}  # market_id -> list of (timestamp, price)

    def _load_state(self) -> Dict:
        if GLITCH_STATE.exists():
            with open(GLITCH_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "glitches_detected": 0,
            "trades_blocked": 0,
            "recent_glitches": [],
            "healthy_markets": [],
            "suspicious_markets": []
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(GLITCH_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_glitch(self, glitch: Dict):
        glitch["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(GLITCH_LOG, 'a') as f:
            f.write(json.dumps(glitch) + "\n")

    def check_price_sanity(self, market_data: Dict) -> Dict:
        """
        Yair's teaching: 'Sanity checks on prices'

        Check if prices are within reasonable bounds.
        """
        result = {
            "market": market_data.get("question", "")[:60],
            "is_sane": True,
            "warnings": [],
            "severity": 0  # 0=ok, 1=warning, 2=danger, 3=block
        }

        prices = json.loads(market_data.get("outcomePrices", "[]"))
        if len(prices) < 2:
            result["is_sane"] = False
            result["warnings"].append("Missing prices")
            result["severity"] = 3
            return result

        yes_price = float(prices[0])
        no_price = float(prices[1])
        total = yes_price + no_price
        spread = abs(1 - total)

        # Check bounds
        if yes_price < SANITY_BOUNDS["min_price"]:
            result["warnings"].append(f"YES price too low: {yes_price}")
            result["severity"] = max(result["severity"], 1)

        if yes_price > SANITY_BOUNDS["max_price"]:
            result["warnings"].append(f"YES price too high: {yes_price}")
            result["severity"] = max(result["severity"], 1)

        if spread > SANITY_BOUNDS["max_spread"]:
            result["warnings"].append(f"Spread too wide: {spread:.1%}")
            result["severity"] = max(result["severity"], 2)
            result["is_sane"] = False

        # Impossible state: total way off from 1
        if total < 0.90 or total > 1.10:
            result["warnings"].append(f"Impossible total: {total:.3f}")
            result["severity"] = 3
            result["is_sane"] = False

        return result

    def check_price_movement(self, market_id: str, current_price: float) -> Dict:
        """
        Yair's teaching: 'Detect anomalies (price jump too big?)'
        """
        result = {
            "market_id": market_id,
            "is_normal": True,
            "warnings": [],
            "severity": 0
        }

        now = datetime.now(timezone.utc)

        # Get price history
        if market_id not in self.price_history:
            self.price_history[market_id] = []

        history = self.price_history[market_id]

        # Add current price
        history.append((now.isoformat(), current_price))

        # Keep last 100 prices
        if len(history) > 100:
            history = history[-100:]
            self.price_history[market_id] = history

        if len(history) < 2:
            return result

        # Check recent movements
        for i in range(len(history) - 1, 0, -1):
            ts_str, price = history[i - 1]
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            time_diff = (now - ts).total_seconds()

            price_change = abs(current_price - price)

            # Check 1-minute bound
            if time_diff <= 60:
                if price_change > SANITY_BOUNDS["max_price_change_1m"]:
                    result["warnings"].append(
                        f"Sudden move: {price_change:.1%} in {time_diff:.0f}s"
                    )
                    result["severity"] = max(result["severity"], 2)
                    result["is_normal"] = False
                break

            # Check 5-minute bound
            if time_diff <= 300:
                if price_change > SANITY_BOUNDS["max_price_change_5m"]:
                    result["warnings"].append(
                        f"Large move: {price_change:.1%} in {time_diff:.0f}s"
                    )
                    result["severity"] = max(result["severity"], 1)
                break

        return result

    def check_data_freshness(self, market_data: Dict) -> Dict:
        """
        Yair's teaching: 'Watch for stale prices'
        """
        result = {
            "is_fresh": True,
            "warnings": [],
            "severity": 0
        }

        # Check update timestamp if available
        updated_at = market_data.get("updatedAt") or market_data.get("lastTradeTime")

        if updated_at:
            try:
                update_time = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                age_seconds = (datetime.now(timezone.utc) - update_time).total_seconds()

                if age_seconds > SANITY_BOUNDS["stale_threshold_seconds"]:
                    result["warnings"].append(f"Data is {age_seconds/60:.1f} minutes old")
                    result["severity"] = 1
                    result["is_fresh"] = False

                if age_seconds > SANITY_BOUNDS["stale_threshold_seconds"] * 2:
                    result["severity"] = 2
            except:
                pass

        return result

    def check_liquidity(self, market_data: Dict) -> Dict:
        """
        Yair's teaching: 'Books thin out, spreads widen'
        """
        result = {
            "is_liquid": True,
            "warnings": [],
            "severity": 0
        }

        liquidity = float(market_data.get("liquidity", 0))

        if liquidity < SANITY_BOUNDS["min_liquidity"]:
            result["warnings"].append(f"Low liquidity: ${liquidity:.0f}")
            result["severity"] = 1
            result["is_liquid"] = False

        if liquidity < 10:
            result["severity"] = 2

        return result

    def validate_trade(self, market_data: Dict, market_id: str = None) -> Dict:
        """
        Full validation before trade execution.

        Yair's teaching: 'Validate before acting. Don't execute on glitched data.'
        """
        validation = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "market": market_data.get("question", "")[:60],
            "safe_to_trade": True,
            "checks": {},
            "overall_severity": 0,
            "recommendation": "PROCEED"
        }

        # Run all checks
        prices = json.loads(market_data.get("outcomePrices", "[]"))
        current_price = float(prices[0]) if prices else 0

        checks = {
            "price_sanity": self.check_price_sanity(market_data),
            "data_freshness": self.check_data_freshness(market_data),
            "liquidity": self.check_liquidity(market_data)
        }

        if market_id:
            checks["price_movement"] = self.check_price_movement(market_id, current_price)

        validation["checks"] = checks

        # Aggregate severity
        max_severity = 0
        all_warnings = []

        for check_name, check_result in checks.items():
            max_severity = max(max_severity, check_result.get("severity", 0))
            all_warnings.extend(check_result.get("warnings", []))

        validation["overall_severity"] = max_severity
        validation["all_warnings"] = all_warnings

        # Decision
        if max_severity >= 3:
            validation["safe_to_trade"] = False
            validation["recommendation"] = "BLOCK - Critical glitch detected"
            self.state["trades_blocked"] += 1
        elif max_severity >= 2:
            validation["safe_to_trade"] = False
            validation["recommendation"] = "WAIT - Suspicious data, verify"
        elif max_severity >= 1:
            validation["recommendation"] = "CAUTION - Minor warnings"

        if not validation["safe_to_trade"]:
            self.state["glitches_detected"] += 1
            self._log_glitch({
                "type": "trade_blocked",
                "market": validation["market"],
                "severity": max_severity,
                "warnings": all_warnings
            })

        return validation

    def scan_all_markets(self) -> Dict:
        """Scan all markets for glitches."""
        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "markets_scanned": 0,
            "healthy": [],
            "suspicious": [],
            "dangerous": []
        }

        try:
            response = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"closed": "false", "limit": 50},
                timeout=15
            )

            if response.status_code != 200:
                return results

            markets = response.json()
            results["markets_scanned"] = len(markets)

            for market in markets:
                validation = self.validate_trade(market)
                market_summary = {
                    "market": validation["market"],
                    "severity": validation["overall_severity"],
                    "warnings": validation["all_warnings"]
                }

                if validation["overall_severity"] == 0:
                    results["healthy"].append(market_summary)
                elif validation["overall_severity"] <= 1:
                    results["suspicious"].append(market_summary)
                else:
                    results["dangerous"].append(market_summary)

            self.state["healthy_markets"] = [m["market"] for m in results["healthy"][:20]]
            self.state["suspicious_markets"] = [m["market"] for m in results["suspicious"][:20]]

        except Exception as e:
            print(f"Error scanning markets: {e}")

        return results

    def run_glitch_detection(self) -> Dict:
        """Run full glitch detection cycle."""
        print("=" * 70)
        print("GLITCH DETECTOR")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        print("[YAIR'S TEACHING ON GLITCHES]")
        print("  'Polymarket Can Glitch'")
        print("  'Don't trust single data point'")
        print("  'Validate before acting'")
        print("  'Fail safe > fail fast'")
        print()

        results = {"timestamp": datetime.now(timezone.utc).isoformat()}

        # Scan markets
        print("[MARKET SCAN]")
        scan = self.scan_all_markets()
        results["scan"] = scan

        print(f"  Markets scanned: {scan['markets_scanned']}")
        print(f"  Healthy: {len(scan['healthy'])}")
        print(f"  Suspicious: {len(scan['suspicious'])}")
        print(f"  Dangerous: {len(scan['dangerous'])}")
        print()

        # Show suspicious markets
        if scan["suspicious"]:
            print("[SUSPICIOUS MARKETS]")
            for m in scan["suspicious"][:5]:
                print(f"  ⚠️ {m['market'][:50]}...")
                for w in m["warnings"]:
                    print(f"     Warning: {w}")
            print()

        # Show dangerous markets
        if scan["dangerous"]:
            print("[DANGEROUS MARKETS - DO NOT TRADE]")
            for m in scan["dangerous"][:5]:
                print(f"  🚫 {m['market'][:50]}...")
                for w in m["warnings"]:
                    print(f"     DANGER: {w}")
            print()

        # Sanity bounds reference
        print("[SANITY BOUNDS]")
        for bound, value in SANITY_BOUNDS.items():
            print(f"  {bound}: {value}")
        print()

        # Summary
        print("=" * 70)
        print("GLITCH DETECTION SUMMARY")
        print("=" * 70)
        print(f"  Total glitches detected: {self.state['glitches_detected']}")
        print(f"  Trades blocked: {self.state['trades_blocked']}")
        print()

        print("SAFE TO TRADE:")
        for market in scan["healthy"][:5]:
            print(f"  ✓ {market['market'][:50]}...")

        self._save_state()
        return results


def main():
    detector = GlitchDetector()
    return detector.run_glitch_detection()


if __name__ == "__main__":
    main()
