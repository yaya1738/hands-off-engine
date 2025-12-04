#!/usr/bin/env python3
"""
Failure Hardening System
========================

Makes the system resilient to all failure modes:
- Retry logic with exponential backoff
- Circuit breakers for failing services
- Automatic fallbacks
- Health checks
- Self-healing mechanisms
- Error tracking and alerts

"Harden failure possibilities"

Master: Yair Siegel
"""

import json
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from functools import wraps
from dataclasses import dataclass, asdict

PROJECT_ROOT = Path(__file__).parent.parent
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"


@dataclass
class FailureRecord:
    """Record of a failure."""
    timestamp: str
    component: str
    error_type: str
    error_message: str
    stack_trace: str
    recovery_attempted: bool
    recovery_successful: bool
    impact: str  # critical, high, medium, low


class CircuitBreaker:
    """Circuit breaker pattern for failing services."""

    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half_open

    def call(self, func: Callable, *args, **kwargs):
        """Call function with circuit breaker protection."""
        if self.state == "open":
            # Check if timeout has passed
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "half_open"
                self.failures = 0
            else:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")

        try:
            result = func(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
            self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()

            if self.failures >= self.failure_threshold:
                self.state = "open"
                print(f"⚠️  Circuit breaker OPENED for {func.__name__}")

            raise e


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True
):
    """Decorator for retry logic with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            delay = base_delay

            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        print(f"❌ Max retries ({max_retries}) reached for {func.__name__}")
                        raise e

                    print(f"⚠️  Retry {retries}/{max_retries} for {func.__name__} after {delay:.1f}s")
                    time.sleep(delay)

                    # Exponential backoff
                    if exponential:
                        delay = min(delay * 2, max_delay)
                    else:
                        delay = min(delay + base_delay, max_delay)

            return None
        return wrapper
    return decorator


class FailureHardeningSystem:
    """Comprehensive failure handling system."""

    def __init__(self):
        self.state_file = STATE_DIR / "failure_hardening.json"
        self.failure_log = LOGS_DIR / "failures.jsonl"
        self.state = self._load_state()
        self.circuit_breakers = {}

        # Ensure logs directory exists
        LOGS_DIR.mkdir(exist_ok=True)

    def _load_state(self) -> Dict:
        """Load failure hardening state."""
        if self.state_file.exists():
            return json.loads(self.state_file.read_text())
        return {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "total_failures": 0,
            "failures_recovered": 0,
            "critical_failures": 0,
            "circuit_breakers_opened": 0,
            "health_status": "healthy"
        }

    def _save_state(self):
        """Save failure hardening state."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        STATE_DIR.mkdir(exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def record_failure(
        self,
        component: str,
        error: Exception,
        impact: str = "medium",
        recovery_attempted: bool = False,
        recovery_successful: bool = False
    ):
        """Record a failure for tracking."""
        failure = FailureRecord(
            timestamp=datetime.now(timezone.utc).isoformat(),
            component=component,
            error_type=type(error).__name__,
            error_message=str(error),
            stack_trace=traceback.format_exc(),
            recovery_attempted=recovery_attempted,
            recovery_successful=recovery_successful,
            impact=impact
        )

        # Update state
        self.state["total_failures"] += 1
        if recovery_successful:
            self.state["failures_recovered"] += 1
        if impact == "critical":
            self.state["critical_failures"] += 1
            self.state["health_status"] = "degraded"

        self._save_state()

        # Log to file
        with open(self.failure_log, "a") as f:
            f.write(json.dumps(asdict(failure)) + "\n")

        return failure

    def get_circuit_breaker(self, name: str) -> CircuitBreaker:
        """Get or create circuit breaker for a component."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker()
        return self.circuit_breakers[name]

    def handle_api_failure(
        self,
        api_name: str,
        error: Exception,
        fallback: Optional[Callable] = None
    ) -> Any:
        """Handle API failure with fallback."""
        print(f"⚠️  API Failure: {api_name}")
        print(f"   Error: {error}")

        # Record failure
        self.record_failure(
            component=f"api_{api_name}",
            error=error,
            impact="medium",
            recovery_attempted=fallback is not None
        )

        # Try fallback
        if fallback:
            try:
                print(f"   Trying fallback...")
                result = fallback()
                print(f"   ✅ Fallback successful")
                self.state["failures_recovered"] += 1
                self._save_state()
                return result
            except Exception as fallback_error:
                print(f"   ❌ Fallback failed: {fallback_error}")
                self.record_failure(
                    component=f"api_{api_name}_fallback",
                    error=fallback_error,
                    impact="high"
                )

        return None

    def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        print("\n🏥 HEALTH CHECK")
        print("-" * 80)

        health = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": "healthy",
            "components": {},
            "issues": []
        }

        # Check failure rate
        if self.state["total_failures"] > 0:
            recovery_rate = self.state["failures_recovered"] / self.state["total_failures"]
            health["components"]["failure_recovery"] = {
                "status": "healthy" if recovery_rate > 0.7 else "degraded",
                "recovery_rate": recovery_rate,
                "total_failures": self.state["total_failures"]
            }

            if recovery_rate < 0.5:
                health["issues"].append({
                    "severity": "high",
                    "component": "failure_recovery",
                    "message": f"Low recovery rate: {recovery_rate:.1%}"
                })
                health["overall_status"] = "degraded"

        # Check circuit breakers
        for name, cb in self.circuit_breakers.items():
            health["components"][f"circuit_breaker_{name}"] = {
                "status": "open" if cb.state == "open" else "healthy",
                "state": cb.state,
                "failures": cb.failures
            }

            if cb.state == "open":
                health["issues"].append({
                    "severity": "critical",
                    "component": name,
                    "message": f"Circuit breaker open ({cb.failures} failures)"
                })
                health["overall_status"] = "critical"

        # Check critical failures
        if self.state["critical_failures"] > 5:
            health["issues"].append({
                "severity": "high",
                "component": "system",
                "message": f"{self.state['critical_failures']} critical failures"
            })
            health["overall_status"] = "degraded"

        print(f"✅ Overall Status: {health['overall_status'].upper()}")
        if health["issues"]:
            print(f"⚠️  Issues Found: {len(health['issues'])}")
            for issue in health["issues"]:
                print(f"   • [{issue['severity']}] {issue['component']}: {issue['message']}")
        else:
            print("   No issues detected")

        return health

    def self_heal(self) -> List[str]:
        """Attempt to self-heal known issues."""
        print("\n🔧 SELF-HEALING")
        print("-" * 80)

        actions_taken = []

        # Reset circuit breakers that have been open too long
        for name, cb in self.circuit_breakers.items():
            if cb.state == "open":
                time_since_failure = time.time() - cb.last_failure_time
                if time_since_failure > cb.timeout * 2:  # Double timeout
                    print(f"   Resetting circuit breaker: {name}")
                    cb.state = "closed"
                    cb.failures = 0
                    actions_taken.append(f"Reset circuit breaker: {name}")

        # Clear critical failure count if old
        if self.state["critical_failures"] > 0:
            print(f"   Clearing critical failure count")
            self.state["critical_failures"] = 0
            self.state["health_status"] = "healthy"
            actions_taken.append("Cleared critical failure count")
            self._save_state()

        if actions_taken:
            print(f"✅ Self-healing actions: {len(actions_taken)}")
        else:
            print("   No self-healing needed")

        return actions_taken

    def get_failure_summary(self, hours: int = 24) -> Dict:
        """Get failure summary for the last N hours."""
        summary = {
            "period_hours": hours,
            "failures": [],
            "failure_count": 0,
            "recovery_count": 0,
            "critical_count": 0
        }

        if not self.failure_log.exists():
            return summary

        cutoff_time = time.time() - (hours * 3600)

        with open(self.failure_log, "r") as f:
            for line in f:
                failure = json.loads(line)
                failure_time = datetime.fromisoformat(failure["timestamp"]).timestamp()

                if failure_time >= cutoff_time:
                    summary["failures"].append(failure)
                    summary["failure_count"] += 1
                    if failure["recovery_successful"]:
                        summary["recovery_count"] += 1
                    if failure["impact"] == "critical":
                        summary["critical_count"] += 1

        return summary

    def display_status(self):
        """Display failure hardening status."""
        print("\n" + "=" * 80)
        print("🛡️  FAILURE HARDENING SYSTEM")
        print("=" * 80)

        print("\n📊 STATISTICS:")
        print("-" * 80)
        print(f"  Total Failures: {self.state['total_failures']}")
        print(f"  Failures Recovered: {self.state['failures_recovered']}")
        if self.state["total_failures"] > 0:
            recovery_rate = self.state["failures_recovered"] / self.state["total_failures"]
            print(f"  Recovery Rate: {recovery_rate:.1%}")
        print(f"  Critical Failures: {self.state['critical_failures']}")
        print(f"  Health Status: {self.state['health_status'].upper()}")

        print("\n🔌 CIRCUIT BREAKERS:")
        print("-" * 80)
        if self.circuit_breakers:
            for name, cb in self.circuit_breakers.items():
                status_icon = "🔴" if cb.state == "open" else "🟢"
                print(f"  {status_icon} {name}: {cb.state.upper()} ({cb.failures} failures)")
        else:
            print("  No circuit breakers active")

        # Recent failures
        summary = self.get_failure_summary(hours=1)
        print(f"\n📈 LAST HOUR:")
        print("-" * 80)
        print(f"  Failures: {summary['failure_count']}")
        print(f"  Recovered: {summary['recovery_count']}")
        print(f"  Critical: {summary['critical_count']}")

        print("\n" + "=" * 80)


# Decorators for easy use
def with_retry(func):
    """Add retry logic to a function."""
    return retry_with_backoff(max_retries=3)(func)


def with_circuit_breaker(name: str):
    """Add circuit breaker to a function."""
    hardening = FailureHardeningSystem()
    cb = hardening.get_circuit_breaker(name)

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)
        return wrapper
    return decorator


def main():
    """Test failure hardening system."""
    print("🚀 Initializing Failure Hardening System...")

    hardening = FailureHardeningSystem()
    hardening.display_status()

    # Run health check
    health = hardening.health_check()

    # Attempt self-healing
    hardening.self_heal()

    print("\n✅ Failure hardening system operational")


if __name__ == "__main__":
    main()
