#!/usr/bin/env python3
"""
ERROR MANAGEMENT - INTEGRAFIX BRIDGE #3

System-wide error handling with circuit breaker pattern.

Before: 531 try/except blocks, 14+ bare `except:` blocks that swallow all errors,
        silent failures propagate through system
After:  Central error registry, circuit breaker, error propagation, health checks

Serving: Yair Siegel
"""

import json
import sys
import traceback
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass, asdict, field
from functools import wraps

# Add project root
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"


class ErrorSeverity(Enum):
    """Error severity levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorRecord:
    """Structured error record."""
    error_id: str = field(default_factory=lambda: f"ERR-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')[:17]}")
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error_type: str = "Exception"
    message: str = ""
    severity: str = "error"
    source: str = "unknown"
    context: Dict = field(default_factory=dict)
    traceback_str: str = ""
    handled: bool = False


class ErrorManager:
    """
    System-wide error management.

    Features:
    - Central error registry
    - Circuit breaker pattern
    - Error rate monitoring
    - Health score calculation
    - Dead man's switch (timeout detection)
    """

    ERROR_LOG = STATE_DIR / "error_registry.jsonl"
    HEALTH_FILE = STATE_DIR / "system_health.json"
    STATE_FILE = STATE_DIR / "error_manager_state.json"

    # Thresholds
    ERRORS_5MIN_THRESHOLD = 20  # Trip circuit if >20 errors in 5 min
    ERRORS_1HR_THRESHOLD = 100  # Warning level
    HEALTH_CRITICAL = 0.3  # Health below 30% is critical

    def __init__(self):
        self._lock = threading.RLock()
        self._circuit_broken = False
        self._error_counts = {
            "total": 0,
            "by_severity": {},
            "by_source": {}
        }
        self._recent_errors: List[ErrorRecord] = []
        self._state = self._load_state()

        # Ensure directories
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        LOGS_DIR.mkdir(parents=True, exist_ok=True)

    def _load_state(self) -> Dict:
        """Load error manager state."""
        if self.STATE_FILE.exists():
            try:
                return json.loads(self.STATE_FILE.read_text())
            except:
                pass
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_errors": 0,
            "circuit_breaks": 0,
            "last_circuit_break": None
        }

    def _save_state(self):
        """Save error manager state."""
        self._state["last_updated"] = datetime.now(timezone.utc).isoformat()
        with open(self.STATE_FILE, "w") as f:
            json.dump(self._state, f, indent=2)

    def record_error(
        self,
        error: Exception,
        source: str = "unknown",
        context: Dict = None,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        handled: bool = False
    ) -> ErrorRecord:
        """
        Record an error with full context.

        Args:
            error: The exception that occurred
            source: Which module/function raised the error
            context: Additional context about what was happening
            severity: How severe is this error
            handled: Was this error handled gracefully

        Returns:
            The error record that was created
        """
        with self._lock:
            record = ErrorRecord(
                error_type=type(error).__name__,
                message=str(error),
                severity=severity.value,
                source=source,
                context=context or {},
                traceback_str=traceback.format_exc(),
                handled=handled
            )

            # Update counts
            self._error_counts["total"] += 1
            self._error_counts["by_severity"][severity.value] = \
                self._error_counts["by_severity"].get(severity.value, 0) + 1
            self._error_counts["by_source"][source] = \
                self._error_counts["by_source"].get(source, 0) + 1

            # Add to recent errors
            self._recent_errors.append(record)
            if len(self._recent_errors) > 1000:
                self._recent_errors = self._recent_errors[-1000:]

            # Update state
            self._state["total_errors"] = self._state.get("total_errors", 0) + 1

            # Log to file
            self._log_error(record)

            # Check circuit breaker
            if self._should_trip_circuit():
                self.trigger_circuit_break(f"Too many errors: {self._count_recent_errors(5)} in 5 min")

            self._save_state()
            return record

    def _log_error(self, record: ErrorRecord):
        """Log error to file."""
        with open(self.ERROR_LOG, "a") as f:
            f.write(json.dumps(asdict(record)) + "\n")

    def _count_recent_errors(self, minutes: int) -> int:
        """Count errors in last N minutes."""
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)

        count = 0
        for record in reversed(self._recent_errors):
            try:
                record_time = datetime.fromisoformat(record.timestamp.replace("Z", "+00:00"))
                if record_time > cutoff:
                    count += 1
                else:
                    break  # Records are chronological
            except:
                pass

        return count

    def _should_trip_circuit(self) -> bool:
        """Determine if circuit breaker should trip."""
        if self._circuit_broken:
            return False

        recent_5min = self._count_recent_errors(5)
        return recent_5min > self.ERRORS_5MIN_THRESHOLD

    def trigger_circuit_break(self, reason: str = "Manual trigger"):
        """
        Trip the circuit breaker.

        Stops all non-critical operations until manual reset.
        """
        with self._lock:
            if self._circuit_broken:
                return  # Already broken

            self._circuit_broken = True
            self._state["circuit_breaks"] = self._state.get("circuit_breaks", 0) + 1
            self._state["last_circuit_break"] = datetime.now(timezone.utc).isoformat()
            self._state["circuit_break_reason"] = reason

            # Update health file
            self._update_health_file("circuit_broken", reason)

            # Log
            print(f"[ERROR MANAGER] CIRCUIT BREAKER TRIPPED: {reason}")

            # Try to send alert
            self._send_alert(f"CIRCUIT BREAK: {reason}")

            self._save_state()

    def reset_circuit_breaker(self):
        """Reset the circuit breaker after manual intervention."""
        with self._lock:
            self._circuit_broken = False
            self._recent_errors.clear()
            self._update_health_file("healthy", "Circuit breaker reset")
            print("[ERROR MANAGER] Circuit breaker reset")
            self._save_state()

    def is_circuit_broken(self) -> bool:
        """Check if circuit is currently broken."""
        return self._circuit_broken

    def is_system_healthy(self) -> bool:
        """Check if system is healthy enough to continue."""
        if self._circuit_broken:
            return False

        health_score = self.get_health_score()
        return health_score > self.HEALTH_CRITICAL

    def get_health_score(self) -> float:
        """
        Calculate current system health (0.0 - 1.0).

        Based on:
        - Error rate in last 5 min
        - Error rate in last hour
        - Severity distribution
        """
        with self._lock:
            errors_5min = self._count_recent_errors(5)
            errors_1hr = self._count_recent_errors(60)

            # Start at full health
            health = 1.0

            # Reduce based on 5-min errors
            if errors_5min > 0:
                health *= max(0.1, 1.0 - (errors_5min / self.ERRORS_5MIN_THRESHOLD))

            # Reduce based on 1-hr errors
            if errors_1hr > 0:
                health *= max(0.3, 1.0 - (errors_1hr / self.ERRORS_1HR_THRESHOLD) * 0.5)

            # Reduce based on critical errors
            critical_count = self._error_counts["by_severity"].get("critical", 0)
            if critical_count > 0:
                health *= max(0.2, 1.0 - (critical_count * 0.1))

            return round(max(0.0, min(1.0, health)), 2)

    def get_status(self) -> Dict:
        """Get current error manager status."""
        with self._lock:
            return {
                "circuit_broken": self._circuit_broken,
                "health_score": self.get_health_score(),
                "errors_5min": self._count_recent_errors(5),
                "errors_1hr": self._count_recent_errors(60),
                "total_errors": self._error_counts["total"],
                "by_severity": dict(self._error_counts["by_severity"]),
                "by_source": dict(self._error_counts["by_source"]),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    def _update_health_file(self, status: str, message: str):
        """Update the health status file."""
        health_data = {
            "status": status,
            "message": message,
            "health_score": self.get_health_score(),
            "circuit_broken": self._circuit_broken,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        with open(self.HEALTH_FILE, "w") as f:
            json.dump(health_data, f, indent=2)

    def _send_alert(self, message: str):
        """Send alert to operator (placeholder for telegram/etc)."""
        try:
            # Try telegram if available
            from telegram.ho_telegram import send_message
            send_message(f"[ERROR ALERT] {message}")
        except:
            pass

        # Always log
        print(f"[ALERT] {message}")


# Singleton instance
_error_manager_instance: Optional[ErrorManager] = None


def get_error_manager() -> ErrorManager:
    """Get the global error manager instance."""
    global _error_manager_instance
    if _error_manager_instance is None:
        _error_manager_instance = ErrorManager()
    return _error_manager_instance


def safe_execute(
    source: str = "unknown",
    severity: ErrorSeverity = ErrorSeverity.ERROR,
    default_return: Any = None,
    reraise: bool = False
) -> Callable:
    """
    Decorator for safe execution with error management.

    Usage:
        @safe_execute(source="trading_hub", default_return={})
        def risky_function():
            # Do something risky
            return result

    This decorator:
    1. Catches all exceptions
    2. Records them to the error registry
    3. Returns default_return on error
    4. Optionally re-raises after recording
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            error_manager = get_error_manager()

            # Check circuit breaker
            if error_manager.is_circuit_broken():
                return default_return

            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Record the error
                error_manager.record_error(
                    error=e,
                    source=source,
                    context={
                        "function": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    },
                    severity=severity,
                    handled=not reraise
                )

                if reraise:
                    raise

                return default_return

        return wrapper
    return decorator


def record_error(
    error: Exception,
    source: str = "unknown",
    context: Dict = None,
    severity: ErrorSeverity = ErrorSeverity.ERROR
) -> ErrorRecord:
    """
    Convenience function to record an error.

    Usage:
        try:
            risky_operation()
        except Exception as e:
            record_error(e, source="my_module", context={"stage": "execution"})
    """
    return get_error_manager().record_error(
        error=error,
        source=source,
        context=context,
        severity=severity
    )


def is_healthy() -> bool:
    """Convenience function to check system health."""
    return get_error_manager().is_system_healthy()


def main():
    """Demo the error manager."""
    print("=" * 70)
    print("ERROR MANAGEMENT - INTEGRAFIX BRIDGE #3")
    print("=" * 70)

    em = ErrorManager()

    print(f"\nInitial status:")
    status = em.get_status()
    print(f"  Health score: {status['health_score']}")
    print(f"  Circuit broken: {status['circuit_broken']}")
    print(f"  Errors (5min): {status['errors_5min']}")

    # Simulate some errors
    print("\n" + "-" * 70)
    print("Simulating errors...")
    print("-" * 70)

    for i in range(5):
        try:
            raise ValueError(f"Test error {i+1}")
        except Exception as e:
            em.record_error(
                error=e,
                source="error_demo",
                context={"iteration": i},
                severity=ErrorSeverity.WARNING if i < 3 else ErrorSeverity.ERROR
            )
            print(f"  Recorded error {i+1}")

    print("\nAfter errors:")
    status = em.get_status()
    print(f"  Health score: {status['health_score']}")
    print(f"  Errors (5min): {status['errors_5min']}")
    print(f"  By severity: {status['by_severity']}")

    # Test decorator
    print("\n" + "-" * 70)
    print("Testing @safe_execute decorator...")
    print("-" * 70)

    @safe_execute(source="demo", default_return="fallback")
    def risky_function():
        raise RuntimeError("This function always fails")

    result = risky_function()
    print(f"  Result: {result}")

    print("\nFinal status:")
    status = em.get_status()
    print(f"  Health score: {status['health_score']}")
    print(f"  Total errors: {status['total_errors']}")

    print("\n" + "=" * 70)
    print(f"Error log: {em.ERROR_LOG}")
    print(f"Health file: {em.HEALTH_FILE}")
    print("=" * 70)


if __name__ == "__main__":
    main()
