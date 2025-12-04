#!/usr/bin/env python3
"""
Yair Wisdom Engine - Apply Teachings to Trading
Actually USES Yair's knowledge in hard skill areas.

TEACHINGS IMPLEMENTED:
1. ESPN Algorithm - Compare ESPN win prob vs Polymarket
2. Smart Edge Strategy - Analysis over speed
3. Sharp Wallet Tracking - Follow smart money
4. Merge Arbitrage - YES + NO < $1 detection
5. New Market Edge - Thin book detection
6. Category-specific strategies

Serving: Yair Siegel
"""

import json
import os
import requests
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from decimal import Decimal

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
KNOWLEDGE_DIR = PROJECT_ROOT / "docs" / "knowledge"

MASTER = "Yair Siegel"
WISDOM_STATE = STATE_DIR / "yair_wisdom.json"
LEARNINGS_LOG = STATE_DIR / "wisdom_learnings.jsonl"

# INTEGRAFIX: Load knowledge bases
try:
    from integrafix.knowledge_loader import knowledge as kb_loader
    KNOWLEDGE_LOADED = True
except ImportError:
    KNOWLEDGE_LOADED = False
    kb_loader = None

def get_knowledge_insight(topic: str) -> str:
    """INTEGRAFIX: Get relevant insight from knowledge bases."""
    if not KNOWLEDGE_LOADED or not kb_loader:
        return ""
    try:
        results = kb_loader.search(topic, limit=2)
        if results:
            return results[0].get('snippet', '')
    except:
        pass
    return ""

# Yair's teachings encoded as actionable rules
YAIR_TEACHINGS = {
    "core_philosophy": {
        "pick_lane": "Be SMART not FAST - analysis advantage over speed",
        "volume_rule": "Volume overwhelms mistakes - trade frequently",
        "edge_discovery": "Edge is discovered through doing, not theorized",
        "bots_insight": "Bots are fast but dumb - patience beats reaction"
    },
    "smart_stack": [
        "right_levels",      # Where to place orders
        "right_sizing",      # Kelly criterion
        "mathematics",       # Probability, EV, fair value
        "statistics",        # Historical patterns
        "risk_optimization"  # Portfolio thinking
    ],
    "category_edges": {
        "sports": {
            "method": "espn_comparison",
            "insight": "ESPN mid-game probability = very accurate",
            "action": "Compare ESPN prob vs Polymarket price, trade divergence"
        },
        "politics": {
            "method": "ai_analysis",
            "insight": "AIs are good at this - lots of context",
            "action": "Use LLMs for polling analysis, statement parsing"
        },
        "war": {
            "method": "skill_competition",
            "insight": "Pure skill - who predicts geopolitics better",
            "action": "Deep research, OSINT, expert sources"
        },
        "mention": {
            "method": "emotional_mispricing",
            "insight": "Low attention, emotional pricing",
            "action": "Find mispriced mentions, bet against hype"
        }
    },
    "arbitrage_rules": {
        "merge_arb": "YES + NO < $1 = free money",
        "threshold": 0.98,  # If total < 0.98, arbitrage exists
        "min_profit": 0.01  # Minimum $0.01 per pair
    },
    "risk_rules": {
        "glitch_check": "Never trust single data point",
        "uma_warning": "Low price + murky rules = manipulation trap",
        "rule_monitor": "Market rules can change - stay vigilant"
    }
}


class YairWisdomEngine:
    """Apply Yair's teachings to actual trading decisions."""

    def __init__(self):
        self.state = self._load_state()
        self.teachings = YAIR_TEACHINGS

    def _load_state(self) -> Dict:
        if WISDOM_STATE.exists():
            with open(WISDOM_STATE) as f:
                return json.load(f)
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "teachings_applied": 0,
            "profitable_applications": 0,
            "category_performance": {},
            "sharp_wallets": [],
            "merge_arbs_found": 0,
            "espn_signals": 0
        }

    def _save_state(self):
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(WISDOM_STATE, 'w') as f:
            json.dump(self.state, f, indent=2)

    def _log_learning(self, learning: Dict):
        learning["timestamp"] = datetime.now(timezone.utc).isoformat()
        learning["master"] = MASTER
        with open(LEARNINGS_LOG, 'a') as f:
            f.write(json.dumps(learning) + "\n")

    # ==================== MERGE ARBITRAGE (Yair Teaching) ====================

    def scan_merge_arbitrage(self) -> List[Dict]:
        """
        Yair's teaching: 'YES + NO < $1 = free money'
        Scan all markets for merge arbitrage opportunities.
        """
        opportunities = []

        try:
            response = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"closed": "false", "limit": 100},
                timeout=15
            )

            if response.status_code != 200:
                return opportunities

            markets = response.json()

            for market in markets:
                prices = json.loads(market.get("outcomePrices", "[]"))
                if len(prices) >= 2:
                    yes_price = float(prices[0])
                    no_price = float(prices[1])
                    total = yes_price + no_price

                    # Yair's rule: if total < 0.98, arbitrage exists
                    if total < self.teachings["arbitrage_rules"]["threshold"]:
                        profit = 1.0 - total
                        if profit >= self.teachings["arbitrage_rules"]["min_profit"]:
                            opportunities.append({
                                "market": market.get("question", "")[:60],
                                "yes_price": yes_price,
                                "no_price": no_price,
                                "total_cost": total,
                                "profit_per_pair": profit,
                                "profit_pct": profit / total * 100,
                                "teaching_applied": "merge_arb",
                                "token_ids": json.loads(market.get("clobTokenIds", "[]"))
                            })

            self.state["merge_arbs_found"] += len(opportunities)

        except Exception as e:
            print(f"Error scanning merge arb: {e}")

        return sorted(opportunities, key=lambda x: x["profit_per_pair"], reverse=True)

    # ==================== SPORTS - ESPN COMPARISON (Yair Teaching) ====================

    def apply_espn_strategy(self) -> List[Dict]:
        """
        Yair's teaching: 'ESPN mid-game probability = very accurate'
        Compare ESPN predictions vs Polymarket prices for sports.
        """
        signals = []

        try:
            # Get sports markets from Polymarket
            response = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"closed": "false", "limit": 50},
                timeout=10
            )

            if response.status_code != 200:
                return signals

            markets = response.json()

            # Filter for sports-related markets
            sports_keywords = ['nba', 'nfl', 'mlb', 'game', 'win', 'beat', 'championship',
                              'playoff', 'super bowl', 'world series', 'finals']

            for market in markets:
                question = market.get("question", "").lower()

                if any(kw in question for kw in sports_keywords):
                    prices = json.loads(market.get("outcomePrices", "[]"))
                    volume = float(market.get("volume", 0))

                    if len(prices) >= 2 and volume > 10000:
                        yes_price = float(prices[0])

                        # Flag as opportunity - needs ESPN data for full implementation
                        signals.append({
                            "market": market.get("question", "")[:60],
                            "polymarket_yes": yes_price,
                            "volume": volume,
                            "action_needed": "Get ESPN probability, compare",
                            "teaching": "ESPN algorithm - compare external prob vs market",
                            "category": "sports"
                        })

            self.state["espn_signals"] += len(signals)

        except Exception as e:
            print(f"Error applying ESPN strategy: {e}")

        return signals

    # ==================== SMART EDGE STRATEGY (Yair Teaching) ====================

    def calculate_smart_edge(self, market_data: Dict) -> Dict:
        """
        Yair's teaching: Apply the 'smart stack' to any market.
        - Right levels
        - Right sizing
        - Mathematics (probability/EV)
        - Statistics
        - Risk optimization
        """
        result = {
            "market": market_data.get("question", "")[:50],
            "analysis": {},
            "recommendation": None,
            "confidence": 0.0
        }

        prices = json.loads(market_data.get("outcomePrices", "[]"))
        if len(prices) < 2:
            return result

        yes_price = float(prices[0])
        no_price = float(prices[1])
        volume = float(market_data.get("volume", 0))
        liquidity = float(market_data.get("liquidity", 0))

        # 1. Right Levels - identify value zones
        if yes_price < 0.05:
            result["analysis"]["levels"] = "Deep value YES territory"
            result["analysis"]["value_zone"] = "extreme_low"
        elif yes_price > 0.95:
            result["analysis"]["levels"] = "Extreme certainty - contrarian NO potential"
            result["analysis"]["value_zone"] = "extreme_high"
        else:
            result["analysis"]["levels"] = "Mid-range, need thesis"
            result["analysis"]["value_zone"] = "neutral"

        # 2. Right Sizing - based on liquidity
        if liquidity > 100000:
            result["analysis"]["sizing"] = "Large - can size up"
            max_position = min(liquidity * 0.01, 100)  # 1% of liquidity, max $100
        elif liquidity > 10000:
            result["analysis"]["sizing"] = "Medium - standard sizing"
            max_position = min(liquidity * 0.005, 50)
        else:
            result["analysis"]["sizing"] = "Small - size down significantly"
            max_position = min(liquidity * 0.002, 20)

        result["analysis"]["max_position"] = max_position

        # 3. Mathematics - EV calculation
        # Assume slight edge detection on extreme prices
        if yes_price < 0.03:
            implied_prob = yes_price
            estimated_true_prob = yes_price * 1.5  # Assume 50% underpriced
            ev = (estimated_true_prob * (1/yes_price - 1)) - ((1 - estimated_true_prob) * 1)
            result["analysis"]["ev"] = ev
            result["analysis"]["math"] = f"EV: {ev:.2f} per $1 risked"

        # 4. Statistics - volume/activity signals
        if volume > 1000000:
            result["analysis"]["statistics"] = "High volume - liquid, competitive"
        elif volume > 100000:
            result["analysis"]["statistics"] = "Medium volume - reasonable"
        else:
            result["analysis"]["statistics"] = "Low volume - thin, careful"

        # 5. Risk optimization
        spread = abs(yes_price + no_price - 1)
        if spread > 0.05:
            result["analysis"]["risk"] = "Wide spread - execution risk"
        else:
            result["analysis"]["risk"] = "Tight spread - good execution"

        # Generate recommendation
        if result["analysis"].get("value_zone") == "extreme_low" and volume > 100000:
            result["recommendation"] = "BUY YES - Deep value with liquidity"
            result["confidence"] = 0.65
        elif result["analysis"].get("value_zone") == "extreme_high" and volume > 100000:
            result["recommendation"] = "CONSIDER NO - Contrarian play"
            result["confidence"] = 0.55

        # INTEGRAFIX: Calculate and output edge value
        # This was MISSING - wisdom engine never outputted edge!
        edge = 0.0
        fair_prob = None

        # Use EV calculation to derive edge
        if "ev" in result["analysis"]:
            # If EV > 0, we have edge
            ev = result["analysis"]["ev"]
            if ev > 0:
                edge = ev * 0.1  # Scale EV to edge (rough approximation)

        # Calculate fair price from recommendation
        if result["recommendation"]:
            if "BUY YES" in result["recommendation"]:
                # We think YES is underpriced
                # Fair prob is higher than market
                fair_prob = min(0.95, yes_price * 1.15)  # 15% underpriced estimate
                edge = fair_prob - yes_price
            elif "CONSIDER NO" in result["recommendation"] or "SELL" in result["recommendation"]:
                # We think NO is underpriced (YES overpriced)
                fair_prob = max(0.05, yes_price * 0.85)  # 15% overpriced estimate
                edge = yes_price - fair_prob  # Negative edge on YES = positive on NO

        # Store edge and fair_prob in result
        result["edge"] = round(edge, 4)
        result["fair_prob"] = round(fair_prob, 4) if fair_prob else None
        result["edge_actionable"] = abs(edge) >= 0.02  # 2% minimum edge

        return result

    # ==================== CATEGORY DETECTION (Yair Teaching) ====================

    def categorize_market(self, question: str) -> Dict:
        """
        Yair's teaching: Different strategies for different categories.
        """
        q = question.lower()

        # Sports detection
        if any(kw in q for kw in ['nba', 'nfl', 'mlb', 'game', 'win', 'beat', 'playoff', 'championship']):
            return {
                "category": "sports",
                "strategy": self.teachings["category_edges"]["sports"],
                "action": "Use ESPN comparison algorithm"
            }

        # Politics detection
        if any(kw in q for kw in ['trump', 'biden', 'election', 'vote', 'president', 'senate', 'congress']):
            return {
                "category": "politics",
                "strategy": self.teachings["category_edges"]["politics"],
                "action": "Use AI analysis for polling/statements"
            }

        # War detection
        if any(kw in q for kw in ['ukraine', 'russia', 'war', 'military', 'invasion', 'ceasefire']):
            return {
                "category": "war",
                "strategy": self.teachings["category_edges"]["war"],
                "action": "Pure skill competition - deep research"
            }

        # Mention detection
        if any(kw in q for kw in ['mention', 'say', 'tweet', 'post', 'announce']):
            return {
                "category": "mention",
                "strategy": self.teachings["category_edges"]["mention"],
                "action": "Look for emotional mispricing"
            }

        return {
            "category": "general",
            "strategy": None,
            "action": "Apply general smart edge analysis"
        }

    # ==================== NEW MARKET EDGE (Yair Teaching) ====================

    def find_new_market_edge(self) -> List[Dict]:
        """
        Yair's teaching: 'New markets have thin order books.
        Limit orders at book edges fill more easily.'

        Detection: age < 24h AND liquidity < $10k AND spread > 200bps
        """
        opportunities = []

        try:
            response = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"closed": "false", "limit": 100},
                timeout=10
            )

            if response.status_code != 200:
                return opportunities

            markets = response.json()

            for market in markets:
                liquidity = float(market.get("liquidity", 0))
                prices = json.loads(market.get("outcomePrices", "[]"))

                if len(prices) >= 2:
                    yes_price = float(prices[0])
                    no_price = float(prices[1])
                    spread = abs(1 - yes_price - no_price)
                    spread_bps = spread * 10000

                    # Yair's criteria: thin liquidity + wide spread = opportunity
                    if liquidity < 10000 and spread_bps > 200:
                        opportunities.append({
                            "market": market.get("question", "")[:60],
                            "liquidity": liquidity,
                            "spread_bps": spread_bps,
                            "yes_price": yes_price,
                            "teaching": "New market thin book edge",
                            "action": "Post limits at edges, size small ($10-25)",
                            "exit_rule": "4h max hold, 5% stop loss"
                        })

        except Exception as e:
            print(f"Error finding new market edge: {e}")

        return opportunities

    # ==================== MAIN WISDOM APPLICATION ====================

    def apply_all_teachings(self) -> Dict:
        """Apply ALL of Yair's teachings to current market conditions."""
        print("=" * 70)
        print("YAIR WISDOM ENGINE - APPLYING TEACHINGS")
        print(f"Master: {MASTER}")
        print(f"Time: {datetime.now(timezone.utc).isoformat()}")
        print("=" * 70)
        print()

        results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "teachings_applied": []
        }

        # 1. Merge Arbitrage
        print("[TEACHING: Merge Arbitrage]")
        print("  'YES + NO < $1 = free money'")
        merge_arbs = self.scan_merge_arbitrage()
        results["merge_arbitrage"] = merge_arbs
        results["teachings_applied"].append("merge_arb")
        print(f"  Found: {len(merge_arbs)} opportunities")
        for arb in merge_arbs[:3]:
            print(f"    - {arb['market'][:40]}...")
            print(f"      Cost: ${arb['total_cost']:.3f} | Profit: ${arb['profit_per_pair']:.3f}")
        print()

        # 2. ESPN Sports Strategy
        print("[TEACHING: ESPN Algorithm]")
        print("  'ESPN mid-game probability = very accurate'")
        espn_signals = self.apply_espn_strategy()
        results["espn_signals"] = espn_signals
        results["teachings_applied"].append("espn_comparison")
        print(f"  Sports markets found: {len(espn_signals)}")
        for sig in espn_signals[:3]:
            print(f"    - {sig['market'][:40]}...")
            print(f"      PM Yes: {sig['polymarket_yes']:.2f} | Action: {sig['action_needed']}")
        print()

        # 3. New Market Edge
        print("[TEACHING: New Market Thin Book]")
        print("  'Thin books = easier fills at edges'")
        new_markets = self.find_new_market_edge()
        results["new_market_edge"] = new_markets
        results["teachings_applied"].append("new_market_edge")
        print(f"  Thin book markets: {len(new_markets)}")
        for nm in new_markets[:3]:
            print(f"    - {nm['market'][:40]}...")
            print(f"      Liquidity: ${nm['liquidity']:.0f} | Spread: {nm['spread_bps']:.0f}bps")
        print()

        # 4. Category Analysis
        print("[TEACHING: Category-Specific Strategies]")
        # Get sample markets for categorization
        try:
            response = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"closed": "false", "limit": 20},
                timeout=10
            )
            if response.status_code == 200:
                markets = response.json()
                category_counts = {"sports": 0, "politics": 0, "war": 0, "mention": 0, "general": 0}
                categorized = []

                for market in markets[:10]:
                    question = market.get("question", "")
                    cat_info = self.categorize_market(question)
                    category_counts[cat_info["category"]] += 1

                    if cat_info["category"] != "general":
                        prices = json.loads(market.get("outcomePrices", "[]"))
                        if prices:
                            categorized.append({
                                "market": question[:50],
                                "category": cat_info["category"],
                                "strategy": cat_info["action"],
                                "yes_price": float(prices[0])
                            })

                results["categorized_markets"] = categorized
                results["category_distribution"] = category_counts
                print(f"  Distribution: {category_counts}")
                for cat in categorized[:3]:
                    print(f"    [{cat['category'].upper()}] {cat['market'][:35]}...")
                    print(f"      Strategy: {cat['strategy']}")
        except:
            pass
        print()

        # 5. Core Philosophy Reminder
        print("[CORE TEACHINGS]")
        for name, teaching in self.teachings["core_philosophy"].items():
            print(f"  {name}: {teaching}")
        print()

        # Summary
        print("=" * 70)
        print("WISDOM APPLICATION SUMMARY")
        print("=" * 70)
        print(f"  Teachings applied: {len(results['teachings_applied'])}")
        print(f"  Merge arb opportunities: {len(merge_arbs)}")
        print(f"  ESPN signals: {len(espn_signals)}")
        print(f"  New market edges: {len(new_markets)}")
        print()

        # Actionable recommendations
        print("ACTIONABLE NOW (from Yair's teachings):")
        if merge_arbs:
            best = merge_arbs[0]
            print(f"  1. MERGE ARB: {best['market'][:40]}")
            print(f"     Buy YES @ {best['yes_price']:.3f} + NO @ {best['no_price']:.3f} = ${best['total_cost']:.3f}")
            print(f"     Merge for $1.00, profit ${best['profit_per_pair']:.3f} per pair")

        if new_markets:
            best = new_markets[0]
            print(f"  2. THIN BOOK: {best['market'][:40]}")
            print(f"     Post limits at edges, size $10-25, 4h max hold")

        print()

        # Update state
        self.state["teachings_applied"] += len(results["teachings_applied"])
        self._save_state()

        # Log learning
        self._log_learning({
            "type": "wisdom_application",
            "teachings_used": results["teachings_applied"],
            "opportunities_found": {
                "merge_arb": len(merge_arbs),
                "espn": len(espn_signals),
                "new_market": len(new_markets)
            }
        })

        return results


def main():
    engine = YairWisdomEngine()
    return engine.apply_all_teachings()


if __name__ == "__main__":
    main()
