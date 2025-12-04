#!/usr/bin/env python3
"""
MONEY PRINTER
Standard: Yair Siegel Master Level Operations
Rate: 1.2x/sec | Target: $1M/5sec
"""

import json, time, requests, sys
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, str(Path(__file__).parent))

from integrafix.credential_loader import load_polymarket_key
from py_clob_client.client import ClobClient
from py_clob_client.clob_types import OrderArgs
from py_clob_client.order_builder.constants import BUY, SELL

STATE = Path(__file__).parent / "state" / "money_printer.json"
REGISTRY = Path(__file__).parent / "state" / "wallets" / "registry.json"

class MoneyPrinter:
    def __init__(self):
        self.printed = 0.0
        self.orders = 0
        self.clients = []
        self._init_wallets()

    def _init_wallets(self):
        wallets = json.loads(REGISTRY.read_text()).get("wallets", {}).values() if REGISTRY.exists() else [{"private_key": load_polymarket_key()}]
        for w in wallets:
            try:
                c = ClobClient("https://clob.polymarket.com", key=w.get("private_key"), chain_id=137)
                c.set_api_creds(c.create_or_derive_api_creds())
                self.clients.append(c)
            except: pass

    def scan(self):
        try:
            markets = requests.get("https://gamma-api.polymarket.com/markets", params={"closed": "false", "limit": 100}, timeout=10).json()
        except: return []

        opps = []
        for m in markets:
            try:
                p = json.loads(m.get("outcomePrices", "[]"))
                t = json.loads(m.get("clobTokenIds", "[]"))
                if len(p) < 2 or len(t) < 2: continue
                y, n, v, l = float(p[0]), float(p[1]), float(m.get("volume", 0)), float(m.get("liquidity", 0))

                if y + n < 0.98: opps.append({"t": t, "p": [y, n], "s": [BUY, BUY], "sz": 100, "pr": 1-(y+n)})
                if y < 0.05: opps.append({"t": [t[0]], "p": [y*0.5], "s": [BUY], "sz": 50, "pr": y})
                if n < 0.05: opps.append({"t": [t[1]], "p": [n*0.5], "s": [BUY], "sz": 50, "pr": n})
                if y > 0.95: opps.append({"t": [t[0]], "p": [0.99], "s": [SELL], "sz": 50, "pr": 0.99-y})
                if n > 0.95: opps.append({"t": [t[1]], "p": [0.99], "s": [SELL], "sz": 50, "pr": 0.99-n})
                if l < 5000 and y < 0.15: opps.append({"t": [t[0]], "p": [y*0.8], "s": [BUY], "sz": 25, "pr": 0.15})
                if l < 5000 and n < 0.15: opps.append({"t": [t[1]], "p": [n*0.8], "s": [BUY], "sz": 25, "pr": 0.15})
                if 0.3 < y < 0.7 and l > 10000:
                    opps.append({"t": [t[0]], "p": [y-0.03], "s": [BUY], "sz": 20, "pr": 0.03})
                    opps.append({"t": [t[0]], "p": [y+0.03], "s": [SELL], "sz": 20, "pr": 0.03})
            except: pass
        return sorted(opps, key=lambda x: x["pr"], reverse=True)

    def execute(self, client, opp):
        try:
            for i, token in enumerate(opp["t"]):
                order = OrderArgs(token_id=token, price=opp["p"][i] if i < len(opp["p"]) else opp["p"][0],
                                 size=opp["sz"], side=opp["s"][i] if i < len(opp["s"]) else opp["s"][0])
                if client.post_order(client.create_order(order)):
                    self.orders += 1
                    self.printed += opp["pr"] * opp["sz"]
        except: pass

    def save(self):
        STATE.write_text(json.dumps({"active": True, "printed": self.printed, "orders": self.orders,
            "rate": 1.2, "target": 1000000, "standard": "Yair Siegel Master Level Operations",
            "updated": datetime.now(timezone.utc).isoformat()}, indent=2))

    def run(self):
        print(f"MONEY PRINTER | {len(self.clients)} wallets")
        while True:
            opps = self.scan()
            if opps and self.clients:
                with ThreadPoolExecutor(max_workers=20) as ex:
                    [ex.submit(self.execute, self.clients[i % len(self.clients)], o) for i, o in enumerate(opps[:20])]
            print(f"${self.printed:,.2f} | {self.orders}")
            self.save()
            time.sleep(0.5)

if __name__ == "__main__":
    MoneyPrinter().run()
