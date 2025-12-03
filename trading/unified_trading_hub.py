#!/usr/bin/env python3
"""
UNIFIED TRADING HUB - Single Entry Point for All Trading
=========================================================
This module consolidates the three competing execution pathways:
1. Primary Executor (ho_executor_plan.py)
2. PolymarketActuator (actuators.py)
3. TradingBrain (trading_brain.py)

ALL TRADING MUST GO THROUGH THIS HUB.

Architecture:
- Single execution lock prevents duplicate trades
- Uses PolymarketTrader from executor/polymarket_client.py
- Uses TradingSafeguards from executor/trading_safeguards.py
- Uses unified_ai for master approval
- Proper token ID resolution via gamma API
"""

import os
import sys
import json
import fcntl
import time
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Setup paths
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Core imports
from ai.unified_ai import check_trading_allowed, log_action, get_master, should_execute

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(name)s] %(message)s')

# Lock file for preventing duplicate trades
LOCK_FILE = REPO_ROOT / "state" / ".trading_lock"
TRADE_HISTORY = REPO_ROOT / "state" / "unified_trade_history.jsonl"

# Polymarket minimum order size
MIN_ORDER_USD = 1.0


@dataclass
class TradeRequest:
    """Unified trade request format"""
    market_slug: str
    side: str  # YES or NO
    amount_usd: float
    token_id: Optional[str] = None
    confidence: float = 0.7
    reason: str = ""
    source: str = "unified_hub"


@dataclass
class TradeResult:
    """Unified trade result format"""
    success: bool
    order_id: Optional[str] = None
    message: str = ""
    executed_amount: float = 0.0
    market_slug: str = ""
    side: str = ""
    timestamp: str = ""


class UnifiedTradingHub:
    """
    THE SINGLE ENTRY POINT FOR ALL TRADING.

    Every component that wants to trade MUST use this hub.
    This prevents duplicate trades and ensures consistent safeguards.
    """

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
        LOG.info(f"[UNIFIED HUB] Initialized - Serving {self.master}")

    def _load_components(self):
        """Load trading components"""
        # Load PolymarketTrader
        try:
            from executor.polymarket_client import PolymarketTrader
            # Set env vars if not set
            os.environ.setdefault('POLYMARKET_PRIVATE_KEY',
                '0x644444ab1d39e9074b01f085a27a4bbf5a8536f411b9b2bea04eb3934f038493')
            os.environ.setdefault('POLYMARKET_FUNDER_ADDRESS',
                '0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D')
            self.trader = PolymarketTrader.from_env()
            LOG.info("[UNIFIED HUB] PolymarketTrader loaded")
        except Exception as e:
            LOG.error(f"[UNIFIED HUB] Failed to load trader: {e}")

        # Load TradingSafeguards
        try:
            from executor.trading_safeguards import TradingSafeguards
            self.safeguards = TradingSafeguards()
            LOG.info("[UNIFIED HUB] TradingSafeguards loaded")
        except Exception as e:
            LOG.error(f"[UNIFIED HUB] Failed to load safeguards: {e}")

    def _acquire_lock(self, timeout: float = 30.0) -> bool:
        """Acquire exclusive trading lock"""
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        start = time.time()

        while time.time() - start < timeout:
            try:
                self._lock_fd = open(LOCK_FILE, 'w')
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._lock_fd.write(f"{os.getpid()}\n{datetime.now(timezone.utc).isoformat()}")
                self._lock_fd.flush()
                return True
            except (IOError, OSError):
                time.sleep(0.1)

        return False

    def _release_lock(self):
        """Release trading lock"""
        try:
            if hasattr(self, '_lock_fd') and self._lock_fd:
                fcntl.flock(self._lock_fd.fileno(), fcntl.LOCK_UN)
                self._lock_fd.close()
                self._lock_fd = None
        except:
            pass

    def resolve_token_id(self, market_slug: str, side: str) -> Optional[str]:
        """Resolve market slug to CLOB token ID via gamma API"""
        import requests

        try:
            url = f'https://gamma-api.polymarket.com/markets?slug={market_slug}'
            r = requests.get(url, timeout=10)
            if not r.ok or not r.json():
                LOG.warning(f"[UNIFIED HUB] Failed to fetch market: {market_slug}")
                return None

            market = r.json()[0] if isinstance(r.json(), list) else r.json()
            clob_ids = market.get('clobTokenIds', [])

            if isinstance(clob_ids, str):
                clob_ids = json.loads(clob_ids)

            if len(clob_ids) >= 2:
                # clobTokenIds[0] = YES, clobTokenIds[1] = NO
                token_id = clob_ids[0] if side.upper() == 'YES' else clob_ids[1]
                LOG.info(f"[UNIFIED HUB] Resolved {market_slug} {side} -> {token_id[:20]}...")
                return token_id

        except Exception as e:
            LOG.error(f"[UNIFIED HUB] Token resolution error: {e}")

        return None

    def check_balance(self) -> Tuple[bool, float, str]:
        """Check wallet balance"""
        if not self.safeguards:
            return False, 0, "Safeguards not loaded"

        ok, msg = self.safeguards.check_wallet_balance(0)

        # Parse balance from message
        import re
        match = re.search(r'\$(\d+\.?\d*)', msg)
        balance = float(match.group(1)) if match else 0

        return ok, balance, msg

    def check_all_gates(self, amount: float) -> Tuple[bool, str]:
        """Check all trading gates"""
        # Gate 1: Unified AI approval
        allowed, reason = check_trading_allowed(amount)
        if not allowed:
            return False, f"UNIFIED_AI_BLOCKED: {reason}"

        # Gate 2: Trading mode state
        mode_file = REPO_ROOT / "state" / "trading_mode.json"
        if mode_file.exists():
            with open(mode_file) as f:
                mode = json.load(f)
            if not mode.get("live_trading_enabled", False):
                return False, "TRADING_DISABLED: live_trading_enabled=false"
            if mode.get("auto_paused", False):
                return False, "TRADING_PAUSED: auto_paused=true"

        # Gate 3: Balance check
        ok, balance, msg = self.check_balance()
        if balance < amount:
            return False, f"INSUFFICIENT_BALANCE: ${balance:.2f} < ${amount:.2f}"

        # Gate 4: Safeguards
        if self.safeguards:
            ok, msgs = self.safeguards.check_all_safeguards(amount, "unified_hub")
            if not ok:
                return False, f"SAFEGUARDS_BLOCKED: {'; '.join(msgs)}"

        return True, "ALL_GATES_PASSED"

    def execute_trade(self, request: TradeRequest) -> TradeResult:
        """
        SINGLE ENTRY POINT FOR ALL TRADING.

        All paths (executor, actuator, brain) should call this.
        """
        timestamp = datetime.now(timezone.utc).isoformat()

        # Validate request
        if request.amount_usd < MIN_ORDER_USD:
            return TradeResult(
                success=False,
                message=f"ORDER_TOO_SMALL: ${request.amount_usd:.2f} < ${MIN_ORDER_USD} minimum",
                market_slug=request.market_slug,
                side=request.side,
                timestamp=timestamp
            )

        # Acquire lock to prevent duplicate trades
        if not self._acquire_lock():
            return TradeResult(
                success=False,
                message="LOCK_FAILED: Another trade in progress",
                market_slug=request.market_slug,
                side=request.side,
                timestamp=timestamp
            )

        try:
            # Check all gates
            allowed, reason = self.check_all_gates(request.amount_usd)
            if not allowed:
                return TradeResult(
                    success=False,
                    message=reason,
                    market_slug=request.market_slug,
                    side=request.side,
                    timestamp=timestamp
                )

            # Resolve token ID if not provided
            token_id = request.token_id
            if not token_id or not str(token_id).isdigit():
                token_id = self.resolve_token_id(request.market_slug, request.side)
                if not token_id:
                    return TradeResult(
                        success=False,
                        message=f"TOKEN_RESOLUTION_FAILED: {request.market_slug}",
                        market_slug=request.market_slug,
                        side=request.side,
                        timestamp=timestamp
                    )

            # Execute trade
            if not self.trader:
                return TradeResult(
                    success=False,
                    message="TRADER_NOT_LOADED",
                    market_slug=request.market_slug,
                    side=request.side,
                    timestamp=timestamp
                )

            from py_clob_client.clob_types import OrderType

            LOG.info(f"[UNIFIED HUB] Executing: {request.side} ${request.amount_usd:.2f} on {request.market_slug}")

            response = self.trader.place_market_order_usd(
                token_id=token_id,
                usd_amount=request.amount_usd,
                side="BUY" if request.side.upper() == "YES" else "SELL",
                order_type=OrderType.FOK
            )

            # Parse response
            success = response.get('success', False) or response.get('status') == 'matched'
            order_id = response.get('orderID') or response.get('order_id')

            result = TradeResult(
                success=success,
                order_id=order_id,
                message=f"EXECUTED: {response.get('status', 'unknown')}",
                executed_amount=request.amount_usd if success else 0,
                market_slug=request.market_slug,
                side=request.side,
                timestamp=timestamp
            )

            # Log action
            log_action("unified_hub", f"trade_{request.side}_{request.amount_usd}",
                      f"{'SUCCESS' if success else 'FAILED'}: {request.market_slug}")

            # Record to history
            self._record_trade(request, result)

            return result

        except Exception as e:
            LOG.error(f"[UNIFIED HUB] Trade error: {e}")
            return TradeResult(
                success=False,
                message=f"EXECUTION_ERROR: {str(e)}",
                market_slug=request.market_slug,
                side=request.side,
                timestamp=timestamp
            )
        finally:
            self._release_lock()

    def _record_trade(self, request: TradeRequest, result: TradeResult):
        """Record trade to history"""
        TRADE_HISTORY.parent.mkdir(parents=True, exist_ok=True)

        record = {
            "timestamp": result.timestamp,
            "request": asdict(request),
            "result": asdict(result),
            "master": self.master
        }

        with open(TRADE_HISTORY, 'a') as f:
            f.write(json.dumps(record) + '\n')

    def execute_batch(self, requests: List[TradeRequest]) -> List[TradeResult]:
        """Execute multiple trades (sequentially with lock)"""
        results = []
        for req in requests:
            result = self.execute_trade(req)
            results.append(result)
            if not result.success:
                LOG.warning(f"[UNIFIED HUB] Batch trade failed: {result.message}")
        return results

    def get_status(self) -> Dict:
        """Get hub status"""
        ok, balance, _ = self.check_balance()

        return {
            "master": self.master,
            "trader_loaded": self.trader is not None,
            "safeguards_loaded": self.safeguards is not None,
            "balance": balance,
            "min_order": MIN_ORDER_USD,
            "max_trades": int(balance // MIN_ORDER_USD) if balance else 0
        }


# Singleton accessor
_hub: Optional[UnifiedTradingHub] = None

def get_trading_hub() -> UnifiedTradingHub:
    """Get the unified trading hub singleton"""
    global _hub
    if _hub is None:
        _hub = UnifiedTradingHub()
    return _hub


def trade(market_slug: str, side: str, amount_usd: float, **kwargs) -> TradeResult:
    """Convenience function for quick trades"""
    hub = get_trading_hub()
    request = TradeRequest(
        market_slug=market_slug,
        side=side,
        amount_usd=amount_usd,
        **kwargs
    )
    return hub.execute_trade(request)


if __name__ == "__main__":
    # Test the hub
    hub = get_trading_hub()
    print(f"Hub Status: {hub.get_status()}")
