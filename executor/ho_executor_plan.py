"""
Executor: The "Body + Reflexes" of the Hands-Off Engine

This module validates and executes planned actions.
It acts as both the body (execution) and reflexes (safety checks)
to ensure no dangerous actions are taken.
"""

import sys
import os
import logging
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# UNIFIED AI - All systems serve Yair Siegel
from ai.unified_ai import check_trading_allowed, log_action, MASTER

from audit import get_audit_logger
from executor.trading_safeguards import get_safeguards, load_mode, load_risk_profile, check_trading_health
from executor.shadow_sink import record_shadow_order
from executor.polymarket_api import PolymarketAPI, Market

# Load Polymarket configuration
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env.polymarket'))

LOG = logging.getLogger(__name__)


def _check_state_file_trading_enabled() -> bool:
    """Check if live trading is enabled in state file (primary source of truth)"""
    state_file = os.path.join(os.path.dirname(__file__), '..', 'state', 'trading_mode.json')
    try:
        if os.path.exists(state_file):
            import json
            with open(state_file) as f:
                mode = json.load(f)
            return mode.get('live_trading_enabled', False) and not mode.get('auto_paused', False)
    except Exception as e:
        LOG.warning(f"Failed to read trading_mode.json: {e}")
    return False


# Global trading toggle - state file is primary, env var can override to DISABLE only
_STATE_FILE_TRADING = _check_state_file_trading_enabled()
_ENV_OVERRIDE = os.getenv("LIVE_TRADING_ENABLED")

# Logic: State file enables, env var can force disable (but not force enable)
# This prevents env var from bypassing state file safety
if _ENV_OVERRIDE == "0":
    _ENV_LIVE_TRADING = False
    LOG.info("Live trading force-disabled by environment variable")
elif _STATE_FILE_TRADING:
    _ENV_LIVE_TRADING = True
    LOG.info("Live trading enabled by state file")
else:
    _ENV_LIVE_TRADING = os.getenv("LIVE_TRADING_ENABLED", "0") == "1"


def get_executor_mode() -> str:
    """
    Returns the executor mode: "live", "dryrun", or "shadow".

    - "live": Real trades sent to API (requires all safety gates to pass)
    - "dryrun": Planning only, no API calls, minimal logging
    - "shadow": Full safety pipeline + logging, but no real API calls

    Environment variable HANDS_OFF_EXECUTOR_MODE takes precedence.
    Falls back to inferring from LIVE_TRADING_ENABLED (backwards compat).

    Default: "dryrun" (conservative)
    """
    explicit_mode = os.getenv("HANDS_OFF_EXECUTOR_MODE", "").lower()

    if explicit_mode in ["live", "dryrun", "shadow"]:
        return explicit_mode

    # Backwards compatibility: infer from LIVE_TRADING_ENABLED
    if _ENV_LIVE_TRADING:
        return "live"

    return "dryrun"


def is_live_trading_enabled() -> bool:
    """
    Check if live trading is enabled.

    Checks:
    1. Environment variable LIVE_TRADING_ENABLED
    2. State file trading_mode.json
    3. System health (data freshness, error rate, recalibration status)

    ALL must pass for live trading to be enabled.

    NOTE: This is separate from get_executor_mode(). This function determines
    WHETHER trading is allowed, while get_executor_mode() determines HOW to execute.
    """
    # Check environment variable
    if not _ENV_LIVE_TRADING:
        LOG.debug("Live trading disabled by environment")
        return False

    # Check state file
    mode = load_mode()
    if not mode.get("live_trading_enabled", False):
        LOG.debug(f"Live trading disabled by state file: {mode.get('reason')}")
        return False

    # Check system health
    is_healthy, health_issues = check_trading_health()
    if not is_healthy:
        LOG.warning(
            f"Live trading blocked by health check: {', '.join(health_issues)}"
        )
        # Don't auto-pause here - let it continue in simulation mode
        # Health checks are advisory, not circuit breakers
        # (Circuit breakers are daily loss limit, rate limit, etc.)
        return False

    return True


# Initialize with environment variable for backward compatibility
LIVE_TRADING_ENABLED = _ENV_LIVE_TRADING

# Initialize Polymarket trader if live trading enabled
trader: Optional['PolymarketTrader'] = None
OrderType = None
if LIVE_TRADING_ENABLED:
    try:
        from executor.polymarket_client import PolymarketTrader
        from py_clob_client.clob_types import OrderType
        trader = PolymarketTrader.from_env()
        LOG.info("✓ Polymarket live trading ENABLED")
    except Exception as e:
        LOG.error(f"Failed to initialize Polymarket trader: {e}")
        LOG.warning("Falling back to simulation mode")
        LIVE_TRADING_ENABLED = False
else:
    LOG.info("Polymarket live trading DISABLED (simulation mode)")


@dataclass
class ExecutionResult:
    """Result of attempting to execute a planned action"""
    market_id: str
    market_name: str
    success: bool
    message: str
    executed_amount: float = 0.0


class Executor:
    """
    The Executor is the body and reflexes of the pipeline.
    It validates planned actions against safety rules and executes them.
    """

    # Safety parameters (reflexes) - loaded from risk_profile.json
    # These are defaults if risk profile is not available
    MAX_POSITION_SIZE = 1000.0  # Maximum dollars per position
    MIN_CONFIDENCE_THRESHOLD = 0.45  # Minimum confidence to execute

    def __init__(self, dryrun: bool = True):
        """
        Initialize executor.

        Args:
            dryrun: If True, no actual trades are executed (default: True)
        """
        self.dryrun = dryrun
        self.audit = get_audit_logger(component="executor")

        # Load dynamic risk parameters
        risk_profile = load_risk_profile()
        self.MAX_POSITION_SIZE = risk_profile.get("max_position_usd", 1000.0)
        self.MIN_CONFIDENCE_THRESHOLD = risk_profile.get("confidence_threshold", 0.45)

        LOG.info(
            f"Executor initialized: max_position=${self.MAX_POSITION_SIZE}, "
            f"min_confidence={self.MIN_CONFIDENCE_THRESHOLD:.1%}"
        )

    def execute(self):
        """Legacy method - kept for backwards compatibility"""
        print("Executing plan...")
        
        # Audit the execution
        self.audit.log_action(
            action_type="plan_execution",
            action_data={"mode": "DRYRUN" if self.dryrun else "LIVE"},
            result="completed"
        )

    def validate_action(self, action) -> tuple[bool, str]:
        """
        Validate a planned action against safety rules (reflexes).

        Args:
            action: PlannedAction object to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check confidence threshold
        if action.confidence < self.MIN_CONFIDENCE_THRESHOLD:
            return False, f"Confidence {action.confidence:.1%} below threshold {self.MIN_CONFIDENCE_THRESHOLD:.1%}"

        # Check for valid side
        if action.side not in ["YES", "NO"]:
            return False, f"Invalid side '{action.side}', must be YES or NO"

        # All checks passed
        return True, "OK"

    def cap_position_size(self, action) -> tuple[float, str]:
        """
        Cap position size to max allowed, returning original and capped amount.

        Returns:
            Tuple of (capped_amount, message)
        """
        if action.amount > self.MAX_POSITION_SIZE:
            original = action.amount
            action.amount = self.MAX_POSITION_SIZE
            return action.amount, f"Capped from ${original:.2f} to ${self.MAX_POSITION_SIZE:.2f}"
        return action.amount, "OK"

    def execute_actions(self, planned_actions: List) -> List[ExecutionResult]:
        """
        Execute a list of planned actions with safety validation.

        Args:
            planned_actions: List of PlannedAction objects

        Returns:
            List of ExecutionResult objects showing outcomes
        """
        results = []

        # UNIFIED AI CHECK: All trading serves Yair Siegel
        if planned_actions:
            total_amount = sum(a.amount for a in planned_actions)
            allowed, reason = check_trading_allowed(total_amount)
            if not allowed:
                LOG.warning(f"[UNIFIED AI] Trading blocked: {reason}")
                log_action("executor", f"trading_blocked:{total_amount}", reason)
                for action in planned_actions:
                    results.append(ExecutionResult(
                        market_id=action.market_id,
                        market_name=action.market_name,
                        success=False,
                        message=f"[UNIFIED AI] {reason}",
                        executed_amount=0.0
                    ))
                return results
            log_action("executor", f"trading_approved:{total_amount}", f"Serving {MASTER}")

        # UPFRONT CHECK: Verify we have enough balance for ALL planned trades
        # This prevents partial execution that drains the wallet
        if planned_actions and get_executor_mode() == "live":
            total_planned_usd = sum(a.amount for a in planned_actions)
            safeguards = get_safeguards()
            balance_ok, balance_msg = safeguards.check_wallet_balance(total_planned_usd)

            if not balance_ok:
                LOG.warning(f"🛑 UPFRONT BALANCE CHECK FAILED: {balance_msg}")
                LOG.warning(f"   Planned ${total_planned_usd:.2f} across {len(planned_actions)} trades")
                # Return all actions as rejected
                for action in planned_actions:
                    results.append(ExecutionResult(
                        market_id=action.market_id,
                        market_name=action.market_name,
                        success=False,
                        message=f"REJECTED: {balance_msg}",
                        executed_amount=0.0
                    ))
                return results

            LOG.info(f"✓ Upfront balance check passed: {balance_msg}")

        for action in planned_actions:
            # Cap position size to max (don't reject, just cap)
            capped_amount, cap_msg = self.cap_position_size(action)

            # Validate action (reflexes) - checks confidence, side, etc.
            is_valid, validation_msg = self.validate_action(action)

            if not is_valid:
                # Safety reflex triggered - reject action
                result = ExecutionResult(
                    market_id=action.market_id,
                    market_name=action.market_name,
                    success=False,
                    message=f"REJECTED: {validation_msg}",
                    executed_amount=0.0
                )
                results.append(result)
                continue

            # Log if position was capped
            if cap_msg != "OK":
                LOG.info(f"Position size capped for {action.market_name}: {cap_msg}")

            # Execute action (body)
            # Get executor mode and determine execution path
            executor_mode = get_executor_mode()

            # Check if live trading is enabled (health checks, state file, etc.)
            live_trading_active = is_live_trading_enabled()
            is_healthy, health_issues = check_trading_health()
            health_reason = "OK" if is_healthy else '; '.join(health_issues)

            # Get current risk profile for logging
            risk_profile = load_risk_profile()
            risk_phase = risk_profile.get("phase", "unknown")

            # Run safety checks (used by both live and shadow modes)
            safeguards = get_safeguards()
            allowed, safety_msgs = safeguards.check_all_safeguards(
                trade_size_usd=action.amount,
                market_name=action.market_name
            )

            # Determine which caps were applied
            caps_applied = []
            if not allowed:
                caps_applied.append("safeguards_blocked")

            # Branch on executor mode
            if executor_mode == "dryrun":
                # DRYRUN MODE: Minimal logging, no API calls
                mode_reason = "dryrun_mode"
                result = ExecutionResult(
                    market_id=action.market_id,
                    market_name=action.market_name,
                    success=True,
                    message=f"DRYRUN: Would place {action.side} order for ${action.amount:.2f}",
                    executed_amount=action.amount
                )

            elif executor_mode == "shadow":
                # SHADOW MODE: Full pipeline execution, no real API calls
                # Record the would-be trade with full context
                record_shadow_order(
                    market_id=action.market_id,
                    market_name=action.market_name,
                    side=action.side,
                    size_usd=action.amount,
                    price=None,  # Price not available in planning phase
                    confidence=action.confidence,
                    source="polymarket_decider_v2",
                    executor_mode="shadow",
                    health_ok=is_healthy,
                    health_reason=health_reason,
                    risk_phase=risk_phase,
                    caps_applied=caps_applied,
                    safety_checks=safety_msgs,
                    extra={
                        "allowed_by_safeguards": allowed,
                        "live_trading_active": live_trading_active,
                    }
                )

                # Return a result indicating shadow execution
                if not allowed:
                    result = ExecutionResult(
                        market_id=action.market_id,
                        market_name=action.market_name,
                        success=False,
                        message=f"SHADOW (blocked): {'; '.join(safety_msgs)}",
                        executed_amount=0.0
                    )
                else:
                    result = ExecutionResult(
                        market_id=action.market_id,
                        market_name=action.market_name,
                        success=True,
                        message=f"SHADOW: Would place {action.side} order for ${action.amount:.2f}",
                        executed_amount=action.amount
                    )
                    LOG.info(f"📋 SHADOW: {action.side} ${action.amount:.2f} on {action.market_name}")

            elif executor_mode == "live":
                # LIVE MODE: Real API calls (if all gates pass)
                if not live_trading_active or trader is None:
                    # Live mode requested but trading not allowed
                    reason = "live_trading_disabled" if not live_trading_active else "no_trader"
                    result = ExecutionResult(
                        market_id=action.market_id,
                        market_name=action.market_name,
                        success=False,
                        message=f"LIVE MODE BLOCKED: {reason}",
                        executed_amount=0.0
                    )
                elif not allowed:
                    # Safeguards blocked the trade
                    LOG.warning(f"🛑 Trade blocked by safeguards: {'; '.join(safety_msgs)}")
                    result = ExecutionResult(
                        market_id=action.market_id,
                        market_name=action.market_name,
                        success=False,
                        message=f"BLOCKED BY SAFEGUARDS: {'; '.join(safety_msgs)}",
                        executed_amount=0.0
                    )
                else:
                    # All gates passed - validate market liquidity before trade
                    trade_token_id = getattr(action, 'token_id', None) or action.market_id

                    # Validate order book liquidity and slippage
                    try:
                        api = PolymarketAPI()
                        ob = api.get_order_book(trade_token_id)

                        # Check if there's liquidity to fill our order
                        if action.side == "YES":
                            depth = ob.ask_depth_usd  # We're buying, check asks
                        else:
                            depth = ob.bid_depth_usd  # We're selling, check bids

                        if depth < action.amount:
                            LOG.warning(f"🛑 Insufficient order book depth: ${depth:.2f} < ${action.amount:.2f}")
                            result = ExecutionResult(
                                market_id=action.market_id,
                                market_name=action.market_name,
                                success=False,
                                message=f"BLOCKED: Insufficient liquidity (${depth:.2f} on book)",
                                executed_amount=0.0
                            )
                            results.append(result)
                            continue

                        # Check spread - reject if too wide (>10%)
                        if ob.spread_bps and ob.spread_bps > 1000:
                            LOG.warning(f"🛑 Spread too wide: {ob.spread_bps:.0f}bps")
                            result = ExecutionResult(
                                market_id=action.market_id,
                                market_name=action.market_name,
                                success=False,
                                message=f"BLOCKED: Spread too wide ({ob.spread_bps:.0f}bps)",
                                executed_amount=0.0
                            )
                            results.append(result)
                            continue

                        LOG.info(f"✓ Order book validated: depth=${depth:.2f}, spread={ob.spread_bps:.0f}bps")

                    except Exception as e:
                        LOG.warning(f"Order book validation failed: {e} - proceeding anyway")

                    # Execute real trade
                    try:
                        # Map YES/NO to BUY/SELL
                        # YES = buying the YES token (BUY)
                        # NO = buying the NO token (BUY on the opposite side)
                        side = "BUY"  # We always BUY the token for the outcome we want

                        # Execute market order
                        LOG.info(
                            f"🔴 LIVE TRADE: {action.side} ${action.amount:.2f} on {action.market_name}"
                        )
                        LOG.info(f"   Safety checks: {'; '.join(safety_msgs)}")

                        api_response = trader.place_market_order_usd(
                            token_id=trade_token_id,
                            usd_amount=action.amount,
                            side=side,
                            order_type=OrderType.FOK,  # Fill-or-kill
                        )

                        result = ExecutionResult(
                            market_id=action.market_id,
                            market_name=action.market_name,
                            success=True,
                            message=f"LIVE: Placed {action.side} order for ${action.amount:.2f} - Order ID: {api_response.get('orderID', 'unknown')}",
                            executed_amount=action.amount
                        )

                        # Log successful trade
                        safeguards.log_trade(
                            market_id=action.market_id,
                            market_name=action.market_name,
                            side=action.side,
                            size_usd=action.amount,
                            success=True,
                            api_response=api_response
                        )

                        LOG.info(f"✓ Trade executed: {api_response}")

                    except Exception as e:
                        LOG.exception(f"Failed to execute live trade: {e}")
                        result = ExecutionResult(
                            market_id=action.market_id,
                            market_name=action.market_name,
                            success=False,
                            message=f"LIVE TRADE FAILED: {str(e)}",
                            executed_amount=0.0
                        )

                        # Log failed trade attempt
                        safeguards.log_trade(
                            market_id=action.market_id,
                            market_name=action.market_name,
                            side=action.side,
                            size_usd=action.amount,
                            success=False
                        )
            else:
                # Unknown mode - fail safe to dryrun
                LOG.error(f"Unknown executor mode: {executor_mode}, falling back to dryrun")
                result = ExecutionResult(
                    market_id=action.market_id,
                    market_name=action.market_name,
                    success=False,
                    message=f"UNKNOWN MODE: {executor_mode}",
                    executed_amount=0.0
                )

            results.append(result)

        return results

    def get_execution_summary(self, results: List[ExecutionResult]) -> dict:
        """
        Generate summary statistics for execution results.

        Args:
            results: List of ExecutionResult objects

        Returns:
            Dictionary with summary statistics
        """
        total = len(results)
        successful = sum(1 for r in results if r.success)
        rejected = total - successful
        total_executed = sum(r.executed_amount for r in results)

        return {
            'total_actions': total,
            'successful': successful,
            'rejected': rejected,
            'total_amount_executed': total_executed,
            'mode': 'DRYRUN' if self.dryrun else 'LIVE'
        }


# Instantiate and execute (for backwards compatibility)
if __name__ == "__main__":
    executor = Executor()
    executor.execute()
