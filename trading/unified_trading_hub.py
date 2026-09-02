#!/usr/bin/env python3
"""Single governed entry point for Polymarket trading.

Credentials are runtime-only. No private key or wallet credential is embedded here.
Every execution passes the unified AI, mode, balance, and safeguard gates.
"""

import fcntl
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))
from ai.unified_ai import check_trading_allowed, get_master, log_action

LOG = logging.getLogger(__name__)
LOCK_FILE = REPO_ROOT / "state" / ".trading_lock"
TRADE_HISTORY = REPO_ROOT / "state" / "unified_trade_history.jsonl"
MIN_ORDER_USD = 1.0


@dataclass
class TradeRequest:
    market_slug: str
    side: str
    amount_usd: float
    token_id: Optional[str] = None
    confidence: float = 0.7
    reason: str = ""
    source: str = "unified_hub"


@dataclass
class TradeResult:
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    executed_amount: float = 0.0
    market_slug: str = ""
    side: str = ""
    timestamp: str = ""


class UnifiedTradingHub:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.master = get_master()
        self.trader = None
        self.safeguards = None
        self._load_components()

    def _load_components(self):
        try:
            if not os.getenv("POLYMARKET_PRIVATE_KEY"):
                LOG.warning("[UNIFIED HUB] Polymarket credential not configured; trading disabled")
                return
            from executor.polymarket_client import PolymarketTrader
            self.trader = PolymarketTrader.from_env()
        except Exception as exc:
            LOG.error("[UNIFIED HUB] Failed to load trader: %s", exc)
        try:
            from executor.trading_safeguards import TradingSafeguards
            self.safeguards = TradingSafeguards()
        except Exception as exc:
            LOG.error("[UNIFIED HUB] Failed to load safeguards: %s", exc)

    def _acquire_lock(self, timeout: float = 30.0) -> bool:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        start = time.time()
        while time.time() - start < timeout:
            try:
                self._lock_fd = open(LOCK_FILE, "w")
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._lock_fd.write(f"{os.getpid()}\n{datetime.now(timezone.utc).isoformat()}")
                self._lock_fd.flush()
                return True
            except (IOError, OSError):
                time.sleep(0.1)
        return False

    def _release_lock(self):
        try:
            if getattr(self, "_lock_fd", None):
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
                self._lock_fd.close()
                self._lock_fd = None
        except Exception:
            pass

    def resolve_token_id(self, market_slug: str, side: str) -> Optional[str]:
        import requests
        try:
            response = requests.get("https://gamma-api.polymarket.com/markets", params={"slug": market_slug}, timeout=10)
            if not response.ok:
                return None
            payload = response.json()
            market = payload[0] if isinstance(payload, list) and payload else payload
            ids = market.get("clobTokenIds", [])
            if isinstance(ids, str):
                ids = json.loads(ids)
            return ids[0 if side.upper() == "YES" else 1] if len(ids) >= 2 else None
        except Exception:
            return None

    def check_balance(self) -> Tuple[bool, float, str]:
        if not self.safeguards:
            return False, 0.0, "Safeguards not loaded"
        try:
            ok, msg = self.safeguards.check_wallet_balance(0)
            import re
            match = re.search(r"\$(\d+\.?\d*)", msg)
            return ok, float(match.group(1)) if match else 0.0, msg
        except Exception as exc:
            return False, 0.0, str(exc)

    def check_all_gates(self, amount: float) -> Tuple[bool, str]:
        allowed, reason = check_trading_allowed(amount)
        if not allowed:
            return False, f"UNIFIED_AI_BLOCKED: {reason}"
        mode_file = REPO_ROOT / "state" / "trading_mode.json"
        if not mode_file.exists():
            return False, "TRADING_DISABLED: trading_mode.json missing"
        try:
            mode = json.loads(mode_file.read_text())
        except Exception as exc:
            return False, f"TRADING_DISABLED: invalid mode state: {exc}"
        if not mode.get("live_trading_enabled", False):
            return False, "TRADING_DISABLED: live_trading_enabled=false"
        if mode.get("auto_paused", False):
            return False, "TRADING_PAUSED: auto_paused=true"
        ok, balance, msg = self.check_balance()
        if balance < amount:
            return False, f"INSUFFICIENT_BALANCE: ${balance:.2f} < ${amount:.2f}"
        if self.safeguards:
            ok, messages = self.safeguards.check_all_safeguards(amount, "unified_hub")
            if not ok:
                return False, f"SAFEGUARDS_BLOCKED: {'; '.join(messages)}"
        return True, "ALL_GATES_PASSED"

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        timestamp = datetime.now(timezone.utc).isoformat()
        if request.amount_usd < MIN_ORDER_USD:
            return TradeResult(False, message=f"ORDER_TOO_SMALL: ${request.amount_usd:.2f} < ${MIN_ORDER_USD}", market_slug=request.market_slug, side=request.side, timestamp=timestamp)
        if not self._acquire_lock():
            return TradeResult(False, message="LOCK_FAILED: Another trade in progress", market_slug=request.market_slug, side=request.side, timestamp=timestamp)
        try:
            allowed, reason = self.check_all_gates(request.amount_usd)
            if not allowed:
                return TradeResult(False, message=reason, market_slug=request.market_slug, side=request.side, timestamp=timestamp)
            if not self.trader:
                return TradeResult(False, message="TRADER_NOT_LOADED: runtime credential required", market_slug=request.market_slug, side=request.side, timestamp=timestamp)
            token_id = request.token_id or self.resolve_token_id(request.market_slug, request.side)
            if not token_id:
                return TradeResult(False, message="TOKEN_RESOLUTION_FAILED", market_slug=request.market_slug, side=request.side, timestamp=timestamp)
            from py_clob_client.clob_types import OrderType
            response = self.trader.place_market_order_usd(token_id=token_id, usd_amount=request.amount_usd, side="BUY" if request.side.upper() == "YES" else "SELL", order_type=OrderType.FOK)
            success = bool(response.get("success")) or response.get("status") == "matched"
            result = TradeResult(success, response.get("orderID") or response.get("order_id"), f"EXECUTED: {response.get('status', 'unknown')}" if success else f"FAILED: {response.get('status', 'unknown')}", request.amount_usd if success else 0.0, request.market_slug, request.side, timestamp)
            log_action("unified_hub", f"trade_{request.side}_{request.amount_usd}", "SUCCESS" if success else "FAILED")
            self._record_trade(request, result)
            return result
        except Exception as exc:
            return TradeResult(False, message=f"EXECUTION_ERROR: {exc}", market_slug=request.market_slug, side=request.side, timestamp=timestamp)
        finally:
            self._release_lock()

    def _record_trade(self, request: TradeRequest, result: TradeResult):
        TRADE_HISTORY.parent.mkdir(parents=True, exist_ok=True)
        with TRADE_HISTORY.open("a") as f:
            f.write(json.dumps({"timestamp": result.timestamp, "request": asdict(request), "result": asdict(result), "master": self.master}) + "\n")

    def execute_batch(self, requests: List[TradeRequest]) -> List[TradeResult]:
        return [self.execute_trade(request) for request in requests]

    def get_status(self) -> Dict:
        ok, balance, _ = self.check_balance()
        return {"master": self.master, "trader_loaded": self.trader is not None, "safeguards_loaded": self.safeguards is not None, "balance": balance, "min_order": MIN_ORDER_USD, "max_trades": int(balance // MIN_ORDER_USD) if balance else 0}


_hub: Optional[UnifiedTradingHub] = None

def get_trading_hub() -> UnifiedTradingHub:
    global _hub
    if _hub is None:
        _hub = UnifiedTradingHub()
    return _hub


def trade(market_slug: str, side: str, amount_usd: float, **kwargs) -> TradeResult:
    return get_trading_hub().execute_trade(TradeRequest(market_slug=market_slug, side=side, amount_usd=amount_usd, **kwargs))
