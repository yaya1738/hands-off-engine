#!/usr/bin/env python3
"""Safe actuator boundary for notifications and governed trading.

Credentials are runtime-only. No secrets are embedded in source or defaults.
All trading is delegated to the unified trading hub and its safety gates.
"""

import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
ACTUATOR_STATE = STATE_DIR / "actuator_state.json"
ACTUATOR_LOG = STATE_DIR / "actuator_log.jsonl"


class TelegramActuator:
    """Send Telegram notifications using runtime environment credentials."""

    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")

    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, message: str) -> bool:
        if not self.is_configured():
            return False
        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = urllib.parse.urlencode({"chat_id": self.chat_id, "text": message, "parse_mode": "HTML"}).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=20) as response:
                return bool(json.loads(response.read().decode()).get("ok", False))
        except Exception:
            return False


class PolymarketActuator:
    """Governed Polymarket actuator; credential absence fails closed."""

    def __init__(self):
        self.trader = None
        self._init_trader()

    def _init_trader(self):
        try:
            if not os.getenv("POLYMARKET_PRIVATE_KEY"):
                return
            from executor.polymarket_client import PolymarketTrader
            self.trader = PolymarketTrader.from_env()
        except Exception:
            self.trader = None

    def is_configured(self) -> bool:
        return self.trader is not None

    def check_health(self) -> bool:
        try:
            return bool(self.trader and self.trader.check_health())
        except Exception:
            return False

    def get_open_orders(self) -> list:
        try:
            return self.trader.get_open_orders() if self.trader else []
        except Exception:
            return []

    def get_trades(self) -> list:
        try:
            return self.trader.get_trades() if self.trader else []
        except Exception:
            return []

    def place_market_order(self, token_id: str, usd_amount: float, side: str, force: bool = False, market_slug: str = "") -> Dict:
        """Route every trade through the unified governed trading hub."""
        if not self.trader:
            return {"error": "Trader not initialized; runtime credential required"}
        try:
            from trading.unified_trading_hub import get_trading_hub, TradeRequest
            result = get_trading_hub().execute_trade(TradeRequest(
                market_slug=market_slug or "unknown",
                side="YES" if side.upper() == "BUY" else "NO",
                amount_usd=usd_amount,
                token_id=token_id,
                reason="PolymarketActuator delegation",
                source="actuator",
            ))
            return {"success": result.success, "order_id": result.order_id, "message": result.message, "executed_amount": result.executed_amount}
        except Exception as exc:
            return {"error": str(exc)}


class ActuatorHub:
    """Central actuator facade used by autonomous components."""

    def __init__(self):
        self.telegram = TelegramActuator()
        self.polymarket = PolymarketActuator()
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if ACTUATOR_STATE.exists():
            try:
                return json.loads(ACTUATOR_STATE.read_text())
            except Exception:
                pass
        return {"messages_sent": 0, "trades_executed": 0, "last_action": None, "errors": 0}

    def _save_state(self):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        ACTUATOR_STATE.write_text(json.dumps(self.state, indent=2))

    def _log(self, actuator: str, action: str, success: bool, details: str = ""):
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        with ACTUATOR_LOG.open("a") as f:
            f.write(json.dumps({"timestamp": datetime.now(timezone.utc).isoformat(), "actuator": actuator, "action": action, "success": success, "details": details}) + "\n")

    def status(self) -> Dict:
        return {
            "telegram": {"configured": self.telegram.is_configured(), "ready": self.telegram.is_configured()},
            "polymarket": {"configured": self.polymarket.is_configured(), "healthy": self.polymarket.check_health()},
            "stats": self.state,
        }

    def notify(self, message: str) -> bool:
        success = self.telegram.send(message)
        self._log("telegram", "notify", success, message[:100])
        if success:
            self.state["messages_sent"] += 1
            self.state["last_action"] = "notify"
        else:
            self.state["errors"] += 1
        self._save_state()
        return success

    def notify_evolution(self, cycle: int, action: str, result: str):
        return self.notify(f"<b>Evolution Cycle {cycle}</b>\nAction: {action}\nResult: {result}")

    def notify_income(self, amount: float, source: str):
        return self.notify(f"<b>INCOME DETECTED!</b>\nAmount: ${amount:.2f}\nSource: {source}")

    def trade(self, token_id: str, usd_amount: float = None, side: str = "BUY", force: bool = False, amount: float = None, market_slug: str = "") -> Dict:
        amount = usd_amount if usd_amount is not None else amount
        if amount is None:
            return {"error": "trade amount is required"}
        result = self.polymarket.place_market_order(token_id, float(amount), side, force=force, market_slug=market_slug)
        success = bool(result.get("success"))
        self._log("polymarket", f"trade_{side}", success, str(result.get("message", result.get("error", "")))[:200])
        if success:
            self.state["trades_executed"] += 1
            self.state["last_action"] = f"trade_{side}"
        else:
            self.state["errors"] += 1
        self._save_state()
        return result
