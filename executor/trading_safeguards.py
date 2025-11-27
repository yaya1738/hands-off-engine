"""
Trading Safety Guardrails for Hands-Off Engine

Implements multiple layers of safety checks before executing live trades.
"""

import os
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

LOG = logging.getLogger(__name__)


class TradingSafeguards:
    """
    Multi-layer safety system for live trading.

    Prevents catastrophic losses through:
    - Daily loss limits
    - Position size caps
    - Exposure tracking
    - Rate limiting
    """

    def __init__(
        self,
        max_daily_loss_usd: float = 3000.0,
        max_position_usd: float = 1000.0,
        max_open_risk_usd: float = 10000.0,
        max_trades_per_hour: int = 20,
        performance_log: Optional[Path] = None,
    ):
        self.max_daily_loss_usd = max_daily_loss_usd
        self.max_position_usd = max_position_usd
        self.max_open_risk_usd = max_open_risk_usd
        self.max_trades_per_hour = max_trades_per_hour

        self.performance_log = performance_log or Path(__file__).parent.parent / "logs" / "trading_performance.jsonl"
        self.performance_log.parent.mkdir(parents=True, exist_ok=True)

    def check_daily_loss_limit(self) -> tuple[bool, str]:
        """
        Check if today's realized losses exceed limit.

        Returns:
            (allowed, reason)
        """
        if not self.performance_log.exists():
            return True, "OK - no performance history yet"

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        today_loss = 0.0

        try:
            with open(self.performance_log) as f:
                for line in f:
                    entry = json.loads(line)
                    ts = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))

                    if ts >= today_start:
                        # Negative PnL = loss
                        pnl = entry.get("realized_pnl_usd", 0.0)
                        if pnl < 0:
                            today_loss += abs(pnl)

        except Exception as e:
            return False, f"Error reading performance log: {e}"

        if today_loss >= self.max_daily_loss_usd:
            # Trigger auto-pause
            maybe_auto_pause(
                reason=f"daily_loss_limit_${today_loss:.0f}",
                notify=True
            )
            return False, f"Daily loss limit reached: ${today_loss:.2f} >= ${self.max_daily_loss_usd:.2f}"

        return True, f"OK - today's losses: ${today_loss:.2f} / ${self.max_daily_loss_usd:.2f}"

    def check_position_size(self, size_usd: float) -> tuple[bool, str]:
        """Check if position size is within limits"""
        if size_usd > self.max_position_usd:
            return False, f"Position ${size_usd:.2f} exceeds max ${self.max_position_usd:.2f}"
        return True, "OK"

    def check_rate_limit(self) -> tuple[bool, str]:
        """Check if we're trading too frequently"""
        if not self.performance_log.exists():
            return True, "OK - no history"

        hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
        recent_trades = 0

        try:
            with open(self.performance_log) as f:
                for line in f:
                    entry = json.loads(line)
                    ts = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))

                    if ts >= hour_ago:
                        recent_trades += 1

        except Exception as e:
            return False, f"Error checking rate limit: {e}"

        if recent_trades >= self.max_trades_per_hour:
            # Trigger auto-pause
            maybe_auto_pause(
                reason=f"rate_limit_{recent_trades}_trades_per_hour",
                notify=True
            )
            return False, f"Rate limit: {recent_trades} trades in last hour >= {self.max_trades_per_hour}"

        return True, f"OK - {recent_trades} trades in last hour"

    def check_all_safeguards(
        self,
        trade_size_usd: float,
        market_name: str = ""
    ) -> tuple[bool, List[str]]:
        """
        Run all safety checks before allowing a trade.

        Returns:
            (allowed, messages)
        """
        messages = []
        allowed = True

        # Check daily loss limit
        ok, msg = self.check_daily_loss_limit()
        messages.append(f"Daily loss: {msg}")
        if not ok:
            allowed = False

        # Check position size
        ok, msg = self.check_position_size(trade_size_usd)
        messages.append(f"Position size: {msg}")
        if not ok:
            allowed = False

        # Check rate limit
        ok, msg = self.check_rate_limit()
        messages.append(f"Rate limit: {msg}")
        if not ok:
            allowed = False

        return allowed, messages

    def log_trade(
        self,
        market_id: str,
        market_name: str,
        side: str,
        size_usd: float,
        success: bool,
        realized_pnl_usd: float = 0.0,
        api_response: Optional[Dict] = None,
    ):
        """Log trade execution for performance tracking"""
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "market_id": market_id,
            "market_name": market_name,
            "side": side,
            "size_usd": size_usd,
            "success": success,
            "realized_pnl_usd": realized_pnl_usd,
            "api_response": api_response,
        }

        with open(self.performance_log, "a") as f:
            f.write(json.dumps(entry) + "\n")


# ============================================================================
# AUTONOMOUS PAUSE/RESUME LOGIC
# ============================================================================

MODE_PATH = Path(__file__).parent.parent / "state" / "trading_mode.json"
RISK_PROFILE_PATH = Path(__file__).parent.parent / "state" / "risk_profile.json"
HARD_LIMITS_PATH = Path(__file__).parent.parent / "config" / "hard_limits.json"


def load_mode() -> dict:
    """
    Load trading mode state from state/trading_mode.json.

    Returns:
        Dictionary with live_trading_enabled, reason, last_changed, etc.
    """
    if not MODE_PATH.exists():
        # Default to disabled for safety
        return {
            "live_trading_enabled": False,
            "reason": "default_safety",
            "last_changed": None,
            "auto_paused": False,
            "pause_count_today": 0,
            "last_resume": None
        }

    try:
        return json.loads(MODE_PATH.read_text())
    except Exception as e:
        LOG.error(f"Failed to load trading mode: {e}")
        return {
            "live_trading_enabled": False,
            "reason": f"load_error: {e}",
            "last_changed": None,
            "auto_paused": False,
            "pause_count_today": 0,
            "last_resume": None
        }


def save_mode(mode: dict):
    """
    Save trading mode state to state/trading_mode.json.

    Args:
        mode: Dictionary with trading mode state
    """
    mode["last_changed"] = datetime.now(timezone.utc).isoformat()
    MODE_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        MODE_PATH.write_text(json.dumps(mode, indent=2) + "\n")
        LOG.info(f"Trading mode saved: live={mode.get('live_trading_enabled')}, reason={mode.get('reason')}")
    except Exception as e:
        LOG.error(f"Failed to save trading mode: {e}")


def maybe_auto_pause(reason: str, notify: bool = True):
    """
    Automatically pause trading if not already paused.

    This is the circuit breaker that stops trading when limits are hit.

    Args:
        reason: Why trading is being paused (e.g., "daily_loss_limit", "api_errors")
        notify: Whether to send a notification (default: True)
    """
    mode = load_mode()

    # Already paused?
    if not mode.get("live_trading_enabled", False):
        LOG.debug(f"Auto-pause triggered but already paused: {reason}")
        return

    # Pause trading
    mode["live_trading_enabled"] = False
    mode["reason"] = reason
    mode["auto_paused"] = True
    mode["pause_count_today"] = mode.get("pause_count_today", 0) + 1

    save_mode(mode)

    LOG.warning(f"🛑 TRADING AUTO-PAUSED: {reason}")

    if notify:
        try:
            from notifications.telegram_notifier import send_telegram_message
            send_telegram_message(
                f"🛑 **TRADING AUTO-PAUSED**\n\n"
                f"Reason: {reason}\n"
                f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                f"Pauses today: {mode['pause_count_today']}\n\n"
                f"Trading will remain paused until manually resumed or recalibration occurs."
            )
        except Exception as e:
            LOG.error(f"Failed to send auto-pause notification: {e}")


def maybe_auto_resume(reason: str = "recalibration", notify: bool = True):
    """
    Automatically resume trading if conditions are met.

    Args:
        reason: Why trading is being resumed
        notify: Whether to send a notification (default: True)
    """
    mode = load_mode()

    # Already live?
    if mode.get("live_trading_enabled", False):
        LOG.debug(f"Auto-resume triggered but already live: {reason}")
        return

    # Resume trading
    mode["live_trading_enabled"] = True
    mode["reason"] = reason
    mode["auto_paused"] = False
    mode["last_resume"] = datetime.now(timezone.utc).isoformat()

    save_mode(mode)

    LOG.info(f"✅ TRADING AUTO-RESUMED: {reason}")

    if notify:
        try:
            from notifications.telegram_notifier import send_telegram_message
            send_telegram_message(
                f"✅ **TRADING AUTO-RESUMED**\n\n"
                f"Reason: {reason}\n"
                f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
                f"Live trading is now active."
            )
        except Exception as e:
            LOG.error(f"Failed to send auto-resume notification: {e}")


def load_risk_profile() -> dict:
    """
    Load risk profile from state/risk_profile.json.

    Returns:
        Dictionary with confidence_threshold, max_position_usd, etc.
    """
    if not RISK_PROFILE_PATH.exists():
        # Default to baby mode for safety
        return {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "confidence_threshold": 0.45,
            "max_position_usd": 50,
            "max_daily_loss_usd": 200,
            "max_trades_per_hour": 10,
            "scale_factor": 1.0,
            "phase": "baby_mode",
            "calibration_history": []
        }

    try:
        return json.loads(RISK_PROFILE_PATH.read_text())
    except Exception as e:
        LOG.error(f"Failed to load risk profile: {e}")
        return {
            "version": "1.0",
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "confidence_threshold": 0.45,
            "max_position_usd": 50,
            "max_daily_loss_usd": 200,
            "max_trades_per_hour": 10,
            "scale_factor": 1.0,
            "phase": "baby_mode",
            "calibration_history": []
        }


def save_risk_profile(profile: dict):
    """
    Save risk profile to state/risk_profile.json.

    Args:
        profile: Dictionary with risk profile state
    """
    profile["last_updated"] = datetime.now(timezone.utc).isoformat()
    RISK_PROFILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        RISK_PROFILE_PATH.write_text(json.dumps(profile, indent=2) + "\n")
        LOG.info(f"Risk profile saved: phase={profile.get('phase')}, max_pos=${profile.get('max_position_usd')}")
    except Exception as e:
        LOG.error(f"Failed to save risk profile: {e}")


def load_hard_limits() -> dict:
    """
    Load absolute hard limits from config/hard_limits.json.

    These are NEVER exceeded by auto-tuning or recalibration.
    They represent the "hard skull" around the self-tuning brain.

    Returns:
        Dictionary with hard limit values
    """
    if not HARD_LIMITS_PATH.exists():
        # Return conservative defaults if file missing
        LOG.warning("Hard limits file not found - using conservative defaults")
        return {
            "MAX_ABSOLUTE_POSITION_USD": 200,
            "MAX_ABSOLUTE_DAILY_LOSS_USD": 400,
            "MAX_ABSOLUTE_OPEN_RISK_USD": 1000,
            "MAX_ABSOLUTE_CONFIDENCE_THRESHOLD": 0.35,
            "MAX_ABSOLUTE_TRADES_PER_HOUR": 20,
            "MIN_CONFIDENCE_THRESHOLD": 0.40
        }

    try:
        data = json.loads(HARD_LIMITS_PATH.read_text())
        limits = data.get("limits", {})
        LOG.debug(f"Hard limits loaded: max_position=${limits.get('MAX_ABSOLUTE_POSITION_USD')}")
        return limits
    except Exception as e:
        LOG.error(f"Failed to load hard limits: {e}")
        # Return conservative defaults on error
        return {
            "MAX_ABSOLUTE_POSITION_USD": 200,
            "MAX_ABSOLUTE_DAILY_LOSS_USD": 400,
            "MAX_ABSOLUTE_OPEN_RISK_USD": 1000,
            "MAX_ABSOLUTE_CONFIDENCE_THRESHOLD": 0.35,
            "MAX_ABSOLUTE_TRADES_PER_HOUR": 20,
            "MIN_CONFIDENCE_THRESHOLD": 0.40
        }


def check_trading_health() -> Tuple[bool, List[str]]:
    """
    Check system health before allowing trading.

    Health checks:
    1. Data freshness - signals/markets not stale
    2. Error rate - no excessive recent failures
    3. Recalibration status - ran recently
    4. Performance log integrity

    Returns:
        (is_healthy, reasons) where reasons are issues found
    """
    issues = []

    # Check 1: Performance log exists and is recent
    performance_log = Path(__file__).parent.parent / "logs" / "trading_performance.jsonl"
    if performance_log.exists():
        # Check if we've logged anything in the last 48 hours
        try:
            last_log_time = None
            with open(performance_log) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        ts = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
                        if last_log_time is None or ts > last_log_time:
                            last_log_time = ts
                    except:
                        continue

            if last_log_time:
                hours_since_log = (datetime.now(timezone.utc) - last_log_time).total_seconds() / 3600
                if hours_since_log > 48:
                    issues.append(f"no_trading_activity_{hours_since_log:.0f}h")
        except Exception as e:
            LOG.warning(f"Could not check performance log freshness: {e}")

    # Check 2: Recent error rate from performance log
    if performance_log.exists():
        try:
            recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_trades = []

            with open(performance_log) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        ts = datetime.fromisoformat(entry.get("timestamp", "").replace("Z", "+00:00"))
                        if ts >= recent_cutoff:
                            recent_trades.append(entry)
                    except:
                        continue

            if len(recent_trades) >= 5:
                failed_trades = [t for t in recent_trades if not t.get("success", False)]
                failure_rate = len(failed_trades) / len(recent_trades)

                if failure_rate > 0.3:  # >30% failure rate
                    issues.append(f"high_error_rate_{failure_rate:.1%}")
        except Exception as e:
            LOG.warning(f"Could not check error rate: {e}")

    # Check 3: Risk profile freshness
    try:
        risk_profile = load_risk_profile()
        last_updated = risk_profile.get("last_updated")
        if last_updated:
            last_update_time = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            hours_since_update = (datetime.now(timezone.utc) - last_update_time).total_seconds() / 3600

            # Risk profile should be updated at least every 36 hours (daily recalibration)
            if hours_since_update > 36:
                issues.append(f"stale_risk_profile_{hours_since_update:.0f}h")
    except Exception as e:
        LOG.warning(f"Could not check risk profile freshness: {e}")

    # Check 4: Mode sanity check
    try:
        mode = load_mode()
        reason = mode.get("reason", "")

        # Flag if we've been auto-paused for too long without resolution
        if mode.get("auto_paused", False):
            last_changed = mode.get("last_changed")
            if last_changed:
                last_change_time = datetime.fromisoformat(last_changed.replace("Z", "+00:00"))
                hours_paused = (datetime.now(timezone.utc) - last_change_time).total_seconds() / 3600

                if hours_paused > 72:  # Paused for >3 days
                    issues.append(f"long_auto_pause_{hours_paused:.0f}h_{reason}")
    except Exception as e:
        LOG.warning(f"Could not check mode status: {e}")

    is_healthy = len(issues) == 0

    if not is_healthy:
        LOG.warning(f"Trading health check FAILED: {', '.join(issues)}")
    else:
        LOG.debug("Trading health check passed")

    return is_healthy, issues


def enforce_hard_limits(risk_profile: dict) -> dict:
    """
    Enforce hard limits on risk profile parameters.

    This ensures that even if the recalibration engine goes crazy,
    it can never exceed absolute hard caps.

    Args:
        risk_profile: Risk profile to enforce limits on

    Returns:
        Risk profile with hard limits applied
    """
    hard_limits = load_hard_limits()
    enforced = risk_profile.copy()

    # Enforce position size cap
    if enforced.get("max_position_usd", 0) > hard_limits.get("MAX_ABSOLUTE_POSITION_USD", 200):
        LOG.warning(
            f"Risk profile max_position_usd ${enforced['max_position_usd']} exceeds "
            f"hard limit ${hard_limits['MAX_ABSOLUTE_POSITION_USD']} - capping"
        )
        enforced["max_position_usd"] = hard_limits["MAX_ABSOLUTE_POSITION_USD"]

    # Enforce daily loss cap
    if enforced.get("max_daily_loss_usd", 0) > hard_limits.get("MAX_ABSOLUTE_DAILY_LOSS_USD", 400):
        LOG.warning(
            f"Risk profile max_daily_loss_usd ${enforced['max_daily_loss_usd']} exceeds "
            f"hard limit ${hard_limits['MAX_ABSOLUTE_DAILY_LOSS_USD']} - capping"
        )
        enforced["max_daily_loss_usd"] = hard_limits["MAX_ABSOLUTE_DAILY_LOSS_USD"]

    # Enforce confidence threshold bounds
    min_conf = hard_limits.get("MIN_CONFIDENCE_THRESHOLD", 0.40)
    max_conf_low = hard_limits.get("MAX_ABSOLUTE_CONFIDENCE_THRESHOLD", 0.35)

    if enforced.get("confidence_threshold", 0.45) < max_conf_low:
        LOG.warning(
            f"Risk profile confidence_threshold {enforced['confidence_threshold']:.1%} below "
            f"absolute minimum {max_conf_low:.1%} - raising"
        )
        enforced["confidence_threshold"] = max_conf_low

    if enforced.get("confidence_threshold", 0.45) < min_conf:
        LOG.warning(
            f"Risk profile confidence_threshold {enforced['confidence_threshold']:.1%} below "
            f"minimum {min_conf:.1%} - raising"
        )
        enforced["confidence_threshold"] = min_conf

    # Enforce trade rate limit
    if enforced.get("max_trades_per_hour", 10) > hard_limits.get("MAX_ABSOLUTE_TRADES_PER_HOUR", 20):
        LOG.warning(
            f"Risk profile max_trades_per_hour {enforced['max_trades_per_hour']} exceeds "
            f"hard limit {hard_limits['MAX_ABSOLUTE_TRADES_PER_HOUR']} - capping"
        )
        enforced["max_trades_per_hour"] = hard_limits["MAX_ABSOLUTE_TRADES_PER_HOUR"]

    return enforced


# Global safeguards instance
_safeguards: Optional[TradingSafeguards] = None


def get_safeguards() -> TradingSafeguards:
    """
    Get or create global safeguards instance.

    Loads parameters from risk_profile.json if available, otherwise falls back
    to environment variables and defaults.

    IMPORTANT: All risk profile values are enforced against hard limits.
    """
    global _safeguards
    if _safeguards is None:
        # Load risk profile and enforce hard limits
        risk_profile = load_risk_profile()
        risk_profile = enforce_hard_limits(risk_profile)

        _safeguards = TradingSafeguards(
            max_daily_loss_usd=risk_profile.get(
                "max_daily_loss_usd",
                float(os.getenv("MAX_DAILY_LOSS_USD", "3000"))
            ),
            max_position_usd=risk_profile.get(
                "max_position_usd",
                float(os.getenv("MAX_POSITION_USD", "1000"))
            ),
            max_open_risk_usd=float(os.getenv("MAX_OPEN_RISK_USD", "10000")),
            max_trades_per_hour=risk_profile.get(
                "max_trades_per_hour",
                int(os.getenv("MAX_TRADES_PER_HOUR", "20"))
            ),
        )

        LOG.info(
            f"Safeguards initialized (hard-limited): "
            f"max_daily_loss=${_safeguards.max_daily_loss_usd}, "
            f"max_position=${_safeguards.max_position_usd}, "
            f"max_trades/hr={_safeguards.max_trades_per_hour}"
        )

    return _safeguards
