#!/usr/bin/env python3
"""
Resilience patterns for fault-tolerant operations.

Provides decorators and utilities for:
- Retry with exponential backoff
- Circuit breaker pattern
- Timeout guards
- Rate limiting
"""

import time
import functools
import threading
from typing import Callable, Optional, List, Any, Type
from enum import Enum
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open"""
    pass


class TimeoutError(Exception):
    """Raised when operation times out"""
    pass


def retry(
    max_attempts: int = 3,
    backoff: Optional[List[float]] = None,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
) -> Callable:
    """
    Retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of attempts (including first try)
        backoff: List of wait times between retries (seconds).
                 If None, uses [1, 2, 4, 8, 16]
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback function(attempt, exception)

    Example:
        @retry(max_attempts=4, backoff=[2, 4, 8, 16])
        def fetch_data():
            response = requests.get("https://api.example.com/data")
            response.raise_for_status()
            return response.json()
    """
    if backoff is None:
        backoff = [1, 2, 4, 8, 16]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    result = func(*args, **kwargs)

                    if attempt > 1:
                        logger.info(
                            "retry_success",
                            function=func.__name__,
                            attempt=attempt,
                            max_attempts=max_attempts
                        )

                    return result

                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(
                            "retry_exhausted",
                            function=func.__name__,
                            attempts=attempt,
                            error=str(e),
                            error_type=type(e).__name__
                        )
                        raise

                    wait_time = backoff[min(attempt - 1, len(backoff) - 1)]

                    logger.warning(
                        "retry_attempt",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        wait_seconds=wait_time,
                        error=str(e),
                        error_type=type(e).__name__
                    )

                    if on_retry:
                        on_retry(attempt, e)

                    time.sleep(wait_time)

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker implementation.

    Tracks failures and opens circuit after threshold is reached.
    Automatically tests service recovery after cooldown period.

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests rejected immediately
    - HALF_OPEN: Testing if service recovered

    Example:
        breaker = CircuitBreaker(
            name="polymarket_api",
            failure_threshold=5,
            cooldown=300,
            success_threshold=2
        )

        @breaker.protected
        def fetch_data():
            return api.get_data()
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        cooldown: float = 300,
        success_threshold: int = 2,
        exceptions: tuple = (Exception,)
    ):
        """
        Args:
            name: Identifier for this circuit breaker
            failure_threshold: Number of failures before opening circuit
            cooldown: Seconds to wait before testing recovery (half-open)
            success_threshold: Successful calls needed in half-open to close
            exceptions: Exceptions that count as failures
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown = cooldown
        self.success_threshold = success_threshold
        self.exceptions = exceptions

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.opened_at: Optional[datetime] = None

        self._lock = threading.Lock()

    def _should_attempt(self) -> bool:
        """Check if request should be attempted"""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True

            if self.state == CircuitState.OPEN:
                # Check if cooldown period has elapsed
                if self.opened_at:
                    elapsed = (datetime.now() - self.opened_at).total_seconds()
                    if elapsed >= self.cooldown:
                        logger.info(
                            "circuit_breaker_half_open",
                            name=self.name,
                            cooldown_elapsed=elapsed
                        )
                        self.state = CircuitState.HALF_OPEN
                        self.success_count = 0
                        return True

                return False

            if self.state == CircuitState.HALF_OPEN:
                return True

            return False

    def _record_success(self):
        """Record successful operation"""
        with self._lock:
            if self.state == CircuitState.CLOSED:
                self.failure_count = 0

            elif self.state == CircuitState.HALF_OPEN:
                self.success_count += 1

                if self.success_count >= self.success_threshold:
                    logger.info(
                        "circuit_breaker_closed",
                        name=self.name,
                        success_count=self.success_count,
                        threshold=self.success_threshold
                    )
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    self.opened_at = None

    def _record_failure(self):
        """Record failed operation"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.state == CircuitState.HALF_OPEN:
                logger.warning(
                    "circuit_breaker_reopening",
                    name=self.name,
                    reason="failure_in_half_open"
                )
                self.state = CircuitState.OPEN
                self.opened_at = datetime.now()
                self.success_count = 0

            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    logger.error(
                        "circuit_breaker_opened",
                        name=self.name,
                        failure_count=self.failure_count,
                        threshold=self.failure_threshold
                    )
                    self.state = CircuitState.OPEN
                    self.opened_at = datetime.now()

    def protected(self, func: Callable) -> Callable:
        """Decorator to protect function with circuit breaker"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self._should_attempt():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service is unavailable. Will retry in "
                    f"{self.cooldown - (datetime.now() - self.opened_at).total_seconds():.0f}s"
                )

            try:
                result = func(*args, **kwargs)
                self._record_success()
                return result

            except self.exceptions as e:
                self._record_failure()
                raise

        return wrapper

    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        with self._lock:
            return {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "success_count": self.success_count,
                "failure_threshold": self.failure_threshold,
                "success_threshold": self.success_threshold,
                "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
                "opened_at": self.opened_at.isoformat() if self.opened_at else None,
                "cooldown_seconds": self.cooldown
            }


# Global registry of circuit breakers
_circuit_breakers: dict[str, CircuitBreaker] = {}


def circuit_breaker(
    name: Optional[str] = None,
    failure_threshold: int = 5,
    cooldown: float = 300,
    success_threshold: int = 2,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Circuit breaker decorator.

    Creates or reuses a named circuit breaker.

    Args:
        name: Unique name for circuit breaker. If None, uses function name
        failure_threshold: Failures before opening circuit
        cooldown: Seconds before testing recovery
        success_threshold: Successes needed to close circuit
        exceptions: Exceptions that trigger circuit

    Example:
        @circuit_breaker("polymarket_api", failure_threshold=5, cooldown=300)
        def fetch_polymarket_data():
            return api.get_markets()
    """
    def decorator(func: Callable) -> Callable:
        breaker_name = name or f"{func.__module__}.{func.__name__}"

        # Get or create circuit breaker
        if breaker_name not in _circuit_breakers:
            _circuit_breakers[breaker_name] = CircuitBreaker(
                name=breaker_name,
                failure_threshold=failure_threshold,
                cooldown=cooldown,
                success_threshold=success_threshold,
                exceptions=exceptions
            )

        breaker = _circuit_breakers[breaker_name]
        return breaker.protected(func)

    return decorator


def get_circuit_breaker_status(name: Optional[str] = None) -> dict:
    """
    Get status of circuit breakers.

    Args:
        name: Specific breaker name, or None for all breakers

    Returns:
        Dict with circuit breaker status(es)
    """
    if name:
        if name in _circuit_breakers:
            return _circuit_breakers[name].get_status()
        else:
            return {"error": f"Circuit breaker '{name}' not found"}
    else:
        return {
            "circuit_breakers": {
                name: breaker.get_status()
                for name, breaker in _circuit_breakers.items()
            }
        }


def timeout(seconds: float) -> Callable:
    """
    Timeout decorator for functions.

    Uses threading to enforce timeout. Note: This doesn't stop the
    underlying operation, it just raises TimeoutError if it takes too long.

    Args:
        seconds: Maximum time to wait

    Example:
        @timeout(30)
        def slow_operation():
            time.sleep(60)  # Will raise TimeoutError after 30 seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout=seconds)

            if thread.is_alive():
                logger.error(
                    "operation_timeout",
                    function=func.__name__,
                    timeout_seconds=seconds
                )
                raise TimeoutError(
                    f"Operation '{func.__name__}' timed out after {seconds}s"
                )

            if exception[0]:
                raise exception[0]

            return result[0]

        return wrapper
    return decorator


class RateLimiter:
    """
    Rate limiter using token bucket algorithm.

    Example:
        limiter = RateLimiter(rate=10, per=60)  # 10 calls per 60 seconds

        @limiter.limit
        def api_call():
            return make_request()
    """

    def __init__(self, rate: int, per: float = 1.0):
        """
        Args:
            rate: Number of allowed calls
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
        self._lock = threading.Lock()

    def _check_rate(self) -> bool:
        """Check if rate limit allows operation"""
        with self._lock:
            current = time.time()
            elapsed = current - self.last_check
            self.last_check = current

            # Add tokens based on elapsed time
            self.allowance += elapsed * (self.rate / self.per)

            # Cap at max rate
            if self.allowance > self.rate:
                self.allowance = self.rate

            # Check if we have tokens
            if self.allowance < 1.0:
                return False

            # Consume a token
            self.allowance -= 1.0
            return True

    def limit(self, func: Callable) -> Callable:
        """Decorator to rate limit function"""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            while not self._check_rate():
                wait_time = self.per / self.rate
                logger.debug(
                    "rate_limit_wait",
                    function=func.__name__,
                    wait_seconds=wait_time
                )
                time.sleep(wait_time)

            return func(*args, **kwargs)

        return wrapper


# Convenience function to combine multiple resilience patterns
def resilient(
    retry_attempts: int = 3,
    retry_backoff: Optional[List[float]] = None,
    circuit_name: Optional[str] = None,
    circuit_threshold: int = 5,
    circuit_cooldown: float = 300,
    timeout_seconds: Optional[float] = None,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Combine multiple resilience patterns.

    Applies in order: timeout → circuit breaker → retry

    Example:
        @resilient(
            retry_attempts=4,
            retry_backoff=[2, 4, 8, 16],
            circuit_name="api",
            circuit_threshold=5,
            circuit_cooldown=300,
            timeout_seconds=30
        )
        def fetch_data():
            return api.get_data()
    """
    def decorator(func: Callable) -> Callable:
        # Apply decorators in reverse order (innermost first)
        wrapped = func

        # 1. Retry (innermost)
        wrapped = retry(
            max_attempts=retry_attempts,
            backoff=retry_backoff,
            exceptions=exceptions
        )(wrapped)

        # 2. Circuit breaker
        if circuit_name or circuit_threshold:
            wrapped = circuit_breaker(
                name=circuit_name,
                failure_threshold=circuit_threshold,
                cooldown=circuit_cooldown,
                exceptions=exceptions
            )(wrapped)

        # 3. Timeout (outermost)
        if timeout_seconds:
            wrapped = timeout(timeout_seconds)(wrapped)

        return wrapped

    return decorator


if __name__ == "__main__":
    # Example usage and tests
    import structlog
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer()
        ]
    )

    print("Testing retry decorator...")

    attempt_counter = [0]

    @retry(max_attempts=4, backoff=[1, 2, 4])
    def flaky_function():
        attempt_counter[0] += 1
        if attempt_counter[0] < 3:
            raise ConnectionError(f"Attempt {attempt_counter[0]} failed")
        return "Success!"

    result = flaky_function()
    print(f"Result: {result}, Attempts: {attempt_counter[0]}")

    print("\nTesting circuit breaker...")

    breaker = CircuitBreaker(
        name="test_service",
        failure_threshold=3,
        cooldown=5,
        success_threshold=2
    )

    @breaker.protected
    def failing_service():
        raise ConnectionError("Service unavailable")

    # Trigger failures to open circuit
    for i in range(5):
        try:
            failing_service()
        except (ConnectionError, CircuitBreakerOpenError) as e:
            print(f"Attempt {i+1}: {type(e).__name__}")

    print(f"\nCircuit status: {breaker.get_status()}")

    print("\nTesting timeout...")

    @timeout(2)
    def slow_function():
        time.sleep(5)
        return "Should not reach here"

    try:
        slow_function()
    except TimeoutError as e:
        print(f"Timeout caught: {e}")

    print("\nAll tests complete!")
