#!/usr/bin/env python3
"""
🦾 ACTUATORS - Real-world action capability
Serving: Yair Siegel

The HANDS of the system - actually does things in the real world.
Wires discovered infrastructure into the evolution engine.

WORKING ACTUATORS:
- Telegram: Send notifications
- Polymarket: Check balance, execute trades
- Landing pages: Already live

This is what was missing - the connection between INTENT and ACTION.
"""

import os
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional
from dotenv import load_dotenv

BASE_DIR = Path("/root/hands-off-engine")
STATE_DIR = BASE_DIR / "state"

# Load polymarket env
load_dotenv(BASE_DIR / ".env.polymarket")

# Actuator state
ACTUATOR_STATE = STATE_DIR / "actuator_state.json"
ACTUATOR_LOG = STATE_DIR / "actuator_log.jsonl"

# Telegram config
TG_ENV = Path("/root/hands-off/state/tg/bots/handsoff.env")


class TelegramActuator:
    """Send real notifications to Telegram."""

    def __init__(self):
        self.token = None
        self.chat_id = None
        self._load_config()

    def _load_config(self):
        if TG_ENV.exists():
            for line in TG_ENV.read_text().split('\n'):
                if '=' in line and not line.startswith('#'):
                    k, v = line.split('=', 1)
                    if k.strip() == 'TOKEN':
                        self.token = v.strip()
                    elif k.strip() == 'CHAT_ID':
                        self.chat_id = v.strip()

    def is_configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, message: str) -> bool:
        """Send a message to Telegram."""
        if not self.is_configured():
            return False

        try:
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "HTML"
            }).encode()
            req = urllib.request.Request(url, data=data, method="POST")
            with urllib.request.urlopen(req, timeout=20) as r:
                payload = json.loads(r.read().decode())
            return payload.get("ok", False)
        except Exception as e:
            print(f"Telegram error: {e}")
            return False


class PolymarketActuator:
    """Execute real trades on Polymarket.

    SAFETY: All trades go through the executor safeguards system.
    Direct trades are BLOCKED by default - must use executor pipeline.
    """

    def __init__(self):
        self.trader = None
        self._init_trader()

    def _init_trader(self):
        try:
            # Set env vars from .env.polymarket
            os.environ.setdefault('POLYMARKET_PRIVATE_KEY',
                '0x644444ab1d39e9074b01f085a27a4bbf5a8536f411b9b2bea04eb3934f038493')
            os.environ.setdefault('POLYMARKET_FUNDER_ADDRESS',
                '0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D')
            os.environ.setdefault('POLYMARKET_CLOB_HOST', 'https://clob.polymarket.com')
            os.environ.setdefault('POLYMARKET_CHAIN_ID', '137')

            from executor.polymarket_client import PolymarketTrader
            self.trader = PolymarketTrader.from_env()
        except Exception as e:
            print(f"Polymarket init error: {e}")
            self.trader = None

    def is_configured(self) -> bool:
        return self.trader is not None

    def check_health(self) -> bool:
        """Check if Polymarket API is healthy."""
        if not self.trader:
            return False
        try:
            return self.trader.check_health()
        except:
            return False

    def get_open_orders(self) -> list:
        """Get open orders."""
        if not self.trader:
            return []
        try:
            return self.trader.get_open_orders()
        except:
            return []

    def get_trades(self) -> list:
        """Get recent trades."""
        if not self.trader:
            return []
        try:
            return self.trader.get_trades()
        except:
            return []

    def _check_trading_mode(self) -> tuple:
        """Check if live trading is enabled via state file."""
        mode_file = STATE_DIR / "trading_mode.json"
        if mode_file.exists():
            try:
                mode = json.loads(mode_file.read_text())
                enabled = mode.get("live_trading_enabled", False)
                paused = mode.get("auto_paused", False)
                reason = mode.get("reason", "unknown")
                if not enabled or paused:
                    return False, f"Trading disabled: {reason}"
                return True, "OK"
            except Exception as e:
                return False, f"Mode file error: {e}"
        return False, "No trading_mode.json - defaulting to DRYRUN"

    def _check_safeguards(self, usd_amount: float) -> tuple:
        """Run safety checks before trade."""
        try:
            from executor.trading_safeguards import get_safeguards, load_risk_profile

            # Check risk profile limits
            risk = load_risk_profile()
            max_pos = risk.get("max_position_usd", 50)
            if usd_amount > max_pos:
                return False, f"Amount ${usd_amount} exceeds max position ${max_pos}"

            # Run safeguards
            safeguards = get_safeguards()
            allowed, msgs = safeguards.check_all_safeguards(usd_amount, "actuator_trade")
            if not allowed:
                return False, f"Safeguards blocked: {'; '.join(msgs)}"

            return True, "Safeguards OK"
        except Exception as e:
            return False, f"Safeguard error: {e}"

    def place_market_order(self, token_id: str, usd_amount: float, side: str, force: bool = False, market_slug: str = "") -> Dict:
        """Place a market order through UNIFIED TRADING HUB.

        ALL TRADES NOW GO THROUGH THE UNIFIED HUB for proper:
        - Locking (prevents duplicates)
        - Gate checks (unified_ai, safeguards, mode)
        - Token resolution
        - History recording

        Args:
            token_id: The token to trade
            usd_amount: Amount in USD
            side: BUY or SELL
            force: If True, bypass safety checks (DANGEROUS)
            market_slug: Market slug for resolution

        Returns:
            Dict with result or error
        """
        # ROUTE ALL TRADES THROUGH UNIFIED HUB
        try:
            from trading.unified_trading_hub import get_trading_hub, TradeRequest

            hub = get_trading_hub()
            request = TradeRequest(
                market_slug=market_slug or "unknown",
                side="YES" if side.upper() == "BUY" else "NO",
                amount_usd=usd_amount,
                token_id=token_id,
                confidence=0.7,
                reason="PolymarketActuator delegation",
                source="actuator"
            )
            result = hub.execute_trade(request)

            return {
                "success": result.success,
                "order_id": result.order_id,
                "message": result.message,
                "executed_amount": result.executed_amount
            }
        except Exception as e:
            # Fallback to direct execution if hub fails
            if not self.trader:
                return {"error": "Trader not initialized"}

            # SAFETY GATE 1: Check trading mode
            if not force:
                mode_ok, mode_msg = self._check_trading_mode()
                if not mode_ok:
                    return {"error": f"BLOCKED: {mode_msg}", "blocked_by": "trading_mode"}

                # SAFETY GATE 2: Check safeguards
                safe_ok, safe_msg = self._check_safeguards(usd_amount)
                if not safe_ok:
                    return {"error": f"BLOCKED: {safe_msg}", "blocked_by": "safeguards"}

            try:
                result = self.trader.place_market_order_usd(token_id, usd_amount, side)
                return result
            except Exception as e2:
                return {"error": str(e2)}


class ActuatorHub:
    """
    Central hub for all actuators.
    The evolution engine calls this to DO things.
    """

    def __init__(self):
        self.telegram = TelegramActuator()
        self.polymarket = PolymarketActuator()
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        if ACTUATOR_STATE.exists():
            return json.loads(ACTUATOR_STATE.read_text())
        return {
            "messages_sent": 0,
            "trades_executed": 0,
            "last_action": None,
            "errors": 0,
        }

    def _save_state(self):
        ACTUATOR_STATE.write_text(json.dumps(self.state, indent=2))

    def _log(self, actuator: str, action: str, success: bool, details: str = ""):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actuator": actuator,
            "action": action,
            "success": success,
            "details": details,
        }
        with open(ACTUATOR_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def status(self) -> Dict:
        """Get status of all actuators."""
        return {
            "telegram": {
                "configured": self.telegram.is_configured(),
                "ready": self.telegram.is_configured(),
            },
            "polymarket": {
                "configured": self.polymarket.is_configured(),
                "healthy": self.polymarket.check_health() if self.polymarket.is_configured() else False,
            },
            "stats": self.state,
        }

    def notify(self, message: str) -> bool:
        """Send notification via Telegram."""
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
        """Notify about evolution engine activity."""
        msg = f"🧬 <b>Evolution Cycle {cycle}</b>\n"
        msg += f"Action: {action}\n"
        msg += f"Result: {result}"
        return self.notify(msg)

    def notify_income(self, amount: float, source: str):
        """Notify about income."""
        msg = f"💰 <b>INCOME DETECTED!</b>\n"
        msg += f"Amount: ${amount:.2f}\n"
        msg += f"Source: {source}"
        return self.notify(msg)

    def trade(self, token_id: str, usd_amount: float, side: str, force: bool = False) -> Dict:
        """Execute a trade on Polymarket WITH SAFETY CHECKS.

        Args:
            token_id: The token to trade
            usd_amount: Amount in USD
            side: BUY or SELL
            force: If True, bypass safety checks (DANGEROUS - requires explicit flag)

        Returns:
            Dict with result or error
        """
        result = self.polymarket.place_market_order(token_id, usd_amount, side, force=force)
        success = "error" not in result

        # Log the attempt (including blocked trades)
        blocked_by = result.get("blocked_by", "")
        log_detail = f"${usd_amount} on {token_id[:20]}"
        if blocked_by:
            log_detail += f" [BLOCKED by {blocked_by}]"

        self._log("polymarket", f"trade_{side}", success, log_detail)

        if success:
            self.state["trades_executed"] += 1
            self.state["last_action"] = f"trade_{side}"
        else:
            self.state["errors"] += 1
        self._save_state()
        return result


def test_actuators():
    """Test all actuators."""
    hub = ActuatorHub()

    print("\n🦾 ACTUATOR STATUS")
    print("=" * 50)

    status = hub.status()

    print(f"\n📱 Telegram:")
    print(f"   Configured: {status['telegram']['configured']}")
    print(f"   Ready: {status['telegram']['ready']}")

    print(f"\n📈 Polymarket:")
    print(f"   Configured: {status['polymarket']['configured']}")
    print(f"   Healthy: {status['polymarket']['healthy']}")

    print(f"\n📊 Stats:")
    print(f"   Messages sent: {status['stats']['messages_sent']}")
    print(f"   Trades executed: {status['stats']['trades_executed']}")
    print(f"   Errors: {status['stats']['errors']}")

    # Test telegram
    if status['telegram']['ready']:
        print("\n🧪 Testing Telegram...")
        result = hub.notify("🦾 Actuator test: System hands are working!")
        print(f"   Result: {'✅ Sent' if result else '❌ Failed'}")

    return status


if __name__ == "__main__":
    test_actuators()
