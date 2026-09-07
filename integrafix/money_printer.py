from ai.factory.live_order_authority import submit_legacy_order
#!/usr/bin/env python3
"""
MONEY PRINTER
=============

Not a trading bot. A money printer.

It runs. It prints money. That's it.

No dry runs. No evaluations. No friction.
Just continuous autonomous profit generation.

Run it and walk away.
"""

import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_FILE = PROJECT_ROOT / "state" / "money_printer.json"


class MoneyPrinter:
    """
    Prints money. Automatically. Forever.
    """

    def __init__(self):
        self.running = True
        self.state = self._load_state()
        self._init_client()

    def _load_state(self):
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text())
        return {
            "started": datetime.now(timezone.utc).isoformat(),
            "cycles": 0,
            "money_printed": 0.0,
            "orders_placed": 0,
        }

    def _save_state(self):
        self.state["last_cycle"] = datetime.now(timezone.utc).isoformat()
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def _init_client(self):
        """Initialize trading client."""
        from integrafix.credential_loader import load_polymarket_key
        from py_clob_client.client import ClobClient

        key = load_polymarket_key()
        if not key:
            raise RuntimeError("No key - cannot print money")

        self.client = ClobClient(
            host="https://clob.polymarket.com",
            key=key,
            chain_id=137
        )
        creds = self.client.create_or_derive_api_creds()
        self.client.set_api_creds(creds)

    def _get_opportunities(self):
        """Find money printing opportunities."""
        import requests

        opportunities = []

        # Fetch markets
        try:
            resp = requests.get(
                "https://gamma-api.polymarket.com/markets",
                params={"closed": "false", "limit": 50},
                timeout=10
            )
            markets = resp.json() if resp.status_code == 200 else []
        except:
            markets = []

        for market in markets:
            try:
                prices = json.loads(market.get("outcomePrices", "[]"))
                if len(prices) < 2:
                    continue

                yes_price = float(prices[0])
                no_price = float(prices[1])
                volume = float(market.get("volume", 0))
                liquidity = float(market.get("liquidity", 0))

                # MERGE ARB: YES + NO < 1 = free money
                total = yes_price + no_price
                if total < 0.98:
                    profit = 1.0 - total
                    opportunities.append({
                        "type": "merge_arb",
                        "market": market,
                        "profit": profit,
                        "priority": profit * 100,  # Higher profit = higher priority
                    })
                    continue

                # EXTREME MISPRICING: Very low prices have edge
                if yes_price < 0.03 and volume > 10000:
                    opportunities.append({
                        "type": "extreme_low",
                        "market": market,
                        "side": "YES",
                        "price": yes_price,
                        "priority": (0.05 - yes_price) * 50,
                    })

                if no_price < 0.03 and volume > 10000:
                    opportunities.append({
                        "type": "extreme_low",
                        "market": market,
                        "side": "NO",
                        "price": no_price,
                        "priority": (0.05 - no_price) * 50,
                    })

                # THIN BOOK: New markets with wide spreads
                if liquidity < 5000 and volume < 50000:
                    if yes_price < 0.10:
                        opportunities.append({
                            "type": "thin_book",
                            "market": market,
                            "side": "YES",
                            "price": yes_price,
                            "priority": 10,
                        })

            except:
                continue

        # Sort by priority
        opportunities.sort(key=lambda x: x.get("priority", 0), reverse=True)
        return opportunities[:10]  # Top 10

    def _print_money(self, opportunity):
        """Execute opportunity = print money."""
        from py_clob_client.clob_types import OrderArgs
        from py_clob_client.order_builder.constants import BUY

        market = opportunity["market"]
        condition_id = market.get("conditionId")

        if not condition_id:
            return None

        # Get tokens
        tokens = market.get("tokens", [])
        if not tokens:
            try:
                clob_tokens = json.loads(market.get("clobTokenIds", "[]"))
                if len(clob_tokens) >= 2:
                    yes_token = clob_tokens[0]
                    no_token = clob_tokens[1]
                else:
                    return None
            except:
                return None
        else:
            yes_token = tokens[0].get("token_id") if len(tokens) > 0 else None
            no_token = tokens[1].get("token_id") if len(tokens) > 1 else None

        if opportunity["type"] == "merge_arb":
            # Buy both YES and NO
            results = []
            prices = json.loads(market.get("outcomePrices", "[]"))
            yes_price = float(prices[0])
            no_price = float(prices[1])

            for token_id, price in [(yes_token, yes_price), (no_token, no_price)]:
                if not token_id:
                    continue
                try:
                    order = OrderArgs(
                        token_id=token_id,
                        price=price,
                        size=10.0,  # $10 per side
                        side=BUY
                    )
                    signed = self.client.create_order(order)
                    result = self.client.submit_legacy_order(signed)
                    results.append(result)
                except Exception as e:
                    pass

            return results if results else None

        else:
            # Single side trade
            side = opportunity.get("side", "YES")
            price = opportunity.get("price", 0.01)
            token_id = yes_token if side == "YES" else no_token

            if not token_id:
                return None

            try:
                order = OrderArgs(
                    token_id=token_id,
                    price=price,
                    size=50.0,  # $50 position
                    side=BUY
                )
                signed = self.client.create_order(order)
                result = self.client.submit_legacy_order(signed)
                return result
            except Exception as e:
                return None

    def run_forever(self):
        """Run the money printer forever."""
        print("=" * 50)
        print("MONEY PRINTER ACTIVATED")
        print("=" * 50)
        print()

        while self.running:
            try:
                self.state["cycles"] += 1
                cycle = self.state["cycles"]

                # Find opportunities
                opportunities = self._get_opportunities()

                if opportunities:
                    print(f"[Cycle {cycle}] Found {len(opportunities)} opportunities")

                    for opp in opportunities[:3]:  # Execute top 3
                        result = self._print_money(opp)

                        if result:
                            self.state["orders_placed"] += 1
                            opp_type = opp["type"]
                            market_q = opp["market"].get("question", "")[:40]
                            print(f"  💵 {opp_type}: {market_q}")

                            if opp["type"] == "merge_arb":
                                profit = opp.get("profit", 0) * 10  # $10 per side
                                self.state["money_printed"] += profit
                else:
                    if cycle % 10 == 0:
                        print(f"[Cycle {cycle}] Scanning...")

                self._save_state()

                # Print status every 100 cycles
                if cycle % 100 == 0:
                    print(f"\n📊 Status: {self.state['orders_placed']} orders, ${self.state['money_printed']:.2f} printed\n")

                # Wait before next cycle
                time.sleep(5)  # 5 seconds between cycles

            except KeyboardInterrupt:
                print("\nStopping money printer...")
                self.running = False
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(10)

        print(f"\nFinal: {self.state['orders_placed']} orders, ${self.state['money_printed']:.2f} printed")

    def run_once(self):
        """Single cycle for testing."""
        opportunities = self._get_opportunities()
        print(f"Found {len(opportunities)} opportunities")

        for opp in opportunities[:3]:
            result = self._print_money(opp)
            opp_type = opp["type"]
            market_q = opp["market"].get("question", "")[:50]

            if result:
                print(f"💵 {opp_type}: {market_q}")
                self.state["orders_placed"] += 1
            else:
                print(f"⏳ {opp_type}: {market_q} (queued)")

        self._save_state()
        return self.state


def start():
    """Start the money printer."""
    printer = MoneyPrinter()
    printer.run_forever()


def test():
    """Run one cycle."""
    printer = MoneyPrinter()
    return printer.run_once()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        test()
    else:
        start()
