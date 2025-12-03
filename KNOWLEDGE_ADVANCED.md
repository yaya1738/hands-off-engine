# Hands-Off Engine - Advanced Technical Knowledge
## Deep Dive: Internals, Patterns, Algorithms & Edge Cases

---

# TABLE OF CONTENTS

1. [Evolution Engine Internals](#1-evolution-engine-internals)
2. [Decision Algorithm Deep Dive](#2-decision-algorithm-deep-dive)
3. [State Machine Architecture](#3-state-machine-architecture)
4. [Process Cycling Algorithms](#4-process-cycling-algorithms)
5. [Actuator Implementation Details](#5-actuator-implementation-details)
6. [Trading Safeguards System](#6-trading-safeguards-system)
7. [Infrastructure Auto-Scaling Logic](#7-infrastructure-auto-scaling-logic)
8. [Hardware Decision Engine](#8-hardware-decision-engine)
9. [Self-Healing Algorithms](#9-self-healing-algorithms)
10. [Multi-Agent Coordination](#10-multi-agent-coordination)
11. [Signal Generation Pipeline](#11-signal-generation-pipeline)
12. [Position Sizing Mathematics](#12-position-sizing-mathematics)
13. [Cost Optimization Algorithms](#13-cost-optimization-algorithms)
14. [State Synchronization Protocol](#14-state-synchronization-protocol)
15. [Feedback Loop Mechanics](#15-feedback-loop-mechanics)
16. [Approval Queue System](#16-approval-queue-system)
17. [Edge Cases & Failure Modes](#17-edge-cases--failure-modes)
18. [Performance Optimization](#18-performance-optimization)
19. [Security Implementation](#19-security-implementation)
20. [System Evolution Patterns](#20-system-evolution-patterns)

---

# 1. EVOLUTION ENGINE INTERNALS

## Core Loop Structure

```python
class EvolutionEngine:
    """The brain of the autonomous system."""

    def main_loop(self):
        """
        Main evolution loop - runs forever.

        Cycle:
        1. Gather intelligence from all sources
        2. Synthesize insights
        3. Compare to ALWAYS_OBJECTIVES
        4. Decide next action
        5. Execute via process endpoints
        6. Capture feedback
        7. Log and learn
        8. Sleep and repeat
        """
        while True:
            try:
                # 1. Gather
                intelligence = self.gather_intelligence()

                # 2. Synthesize
                insights = self.synthesize(intelligence)

                # 3. Compare to objectives
                gaps = self.identify_gaps(insights)

                # 4. Decide
                decision = self.decide_action(gaps, insights)

                # 5. Execute
                if decision.action:
                    result = self.execute(decision)
                else:
                    result = None

                # 6. Feedback
                self.capture_feedback(decision, result)

                # 7. Log
                self.log_cycle(intelligence, decision, result)

                # 8. Sleep
                time.sleep(self.cycle_interval)

            except Exception as e:
                self.handle_error(e)
```

## Intelligence Gathering

```python
def gather_intelligence(self) -> Dict:
    """Gather from all input sources."""
    intelligence = {}

    for name, path in INPUTS.items():
        if path.suffix == '.jsonl':
            # Get last N entries from log
            intelligence[name] = self._read_jsonl_tail(path, n=10)
        else:
            # Read JSON state
            intelligence[name] = self._read_json(path)

    return intelligence

def _read_jsonl_tail(self, path: Path, n: int) -> List[Dict]:
    """Read last N lines of JSONL file."""
    if not path.exists():
        return []

    lines = path.read_text().strip().split('\n')
    recent = lines[-n:] if len(lines) > n else lines

    return [json.loads(line) for line in recent if line]
```

## Insight Synthesis

```python
def synthesize(self, intelligence: Dict) -> Dict:
    """Synthesize insights from raw intelligence."""
    insights = {
        "urgent_issues": [],
        "opportunities": [],
        "blockers": [],
        "sentiment": "neutral",
        "priority_actions": [],
    }

    # Check war room for preparations
    if intelligence.get("war_room"):
        for entry in intelligence["war_room"]:
            if entry.get("priority") == "high":
                insights["priority_actions"].append(entry)

    # Check reality for ground truth
    if intelligence.get("reality"):
        reality = intelligence["reality"]
        if reality.get("income") == 0:
            insights["urgent_issues"].append("zero_income")
        if reality.get("errors"):
            insights["blockers"].extend(reality["errors"])

    # Check gallery for sentiment
    if intelligence.get("gallery"):
        sentiments = [e.get("sentiment") for e in intelligence["gallery"]]
        positive = sum(1 for s in sentiments if s == "positive")
        negative = sum(1 for s in sentiments if s == "negative")
        insights["sentiment"] = "positive" if positive > negative else "negative" if negative > positive else "neutral"

    # Check doctor for health
    if intelligence.get("doctor"):
        doctor = intelligence["doctor"]
        if doctor.get("status") == "critical":
            insights["urgent_issues"].insert(0, "system_critical")

    return insights
```

## Decision Algorithm

```python
def decide_action(self, gaps: List, insights: Dict) -> Decision:
    """Decide next action based on gaps and insights."""

    # Priority 1: Critical issues
    if "system_critical" in insights["urgent_issues"]:
        return Decision(
            action="self_heal",
            priority="critical",
            reason="System in critical state"
        )

    # Priority 2: Zero income
    if "zero_income" in insights["urgent_issues"]:
        return Decision(
            action="income_generation",
            priority="high",
            reason="No income being generated"
        )

    # Priority 3: Blockers
    if insights["blockers"]:
        return Decision(
            action="unblock",
            priority="high",
            reason=f"Blockers: {insights['blockers']}"
        )

    # Priority 4: Opportunities
    if insights["opportunities"]:
        best_opp = max(insights["opportunities"], key=lambda x: x.get("score", 0))
        return Decision(
            action="pursue_opportunity",
            priority="medium",
            target=best_opp
        )

    # Default: Continue improvement
    return Decision(
        action="improve",
        priority="low",
        reason="Continuous improvement"
    )
```

---

# 2. DECISION ALGORITHM DEEP DIVE

## Priority Matrix

```
PRIORITY LEVELS:
┌──────────────────────────────────────────────────────┐
│  CRITICAL   │ System failure, trading at risk       │
│  (Immediate)│ Actions: self_heal, protect_trading   │
├─────────────┼────────────────────────────────────────┤
│  HIGH       │ Zero income, major blockers           │
│  (< 1 min)  │ Actions: income_gen, unblock          │
├─────────────┼────────────────────────────────────────┤
│  MEDIUM     │ Opportunities, optimizations          │
│  (< 5 min)  │ Actions: pursue_opp, optimize         │
├─────────────┼────────────────────────────────────────┤
│  LOW        │ Continuous improvement                │
│  (Normal)   │ Actions: improve, learn               │
└─────────────┴────────────────────────────────────────┘
```

## Action Selection Algorithm

```python
def select_action(self, candidates: List[Action]) -> Action:
    """Select best action from candidates using scoring."""

    def score_action(action: Action) -> float:
        score = 0.0

        # Priority weight
        priority_weights = {
            "critical": 1000,
            "high": 100,
            "medium": 10,
            "low": 1
        }
        score += priority_weights.get(action.priority, 0)

        # Expected value
        if action.expected_value:
            score += action.expected_value * 10

        # Success probability
        if action.success_probability:
            score *= action.success_probability

        # Recency penalty (avoid repeating same action)
        if self._recently_done(action.type):
            score *= 0.5

        return score

    # Score all candidates
    scored = [(score_action(a), a) for a in candidates]

    # Select highest scoring
    scored.sort(reverse=True)
    return scored[0][1]
```

## Capability Selection

```python
CAPABILITIES = {
    "outreach": {
        "triggers": ["zero_income", "low_conversions"],
        "cooldown": 300,  # 5 minutes
        "cost": 0,
        "expected_value": 10.0
    },
    "trading": {
        "triggers": ["signal_detected", "opportunity"],
        "cooldown": 60,
        "cost": 0.01,  # Gas + fees
        "expected_value": 5.0
    },
    "self_heal": {
        "triggers": ["error_detected", "health_degraded"],
        "cooldown": 30,
        "cost": 0,
        "expected_value": 100.0  # Prevent losses
    },
    "conversion": {
        "triggers": ["visitors_no_convert"],
        "cooldown": 600,
        "cost": 0,
        "expected_value": 20.0
    }
}

def select_capability(self, trigger: str) -> Optional[str]:
    """Select capability based on trigger."""
    for cap_name, cap in CAPABILITIES.items():
        if trigger in cap["triggers"]:
            if not self._in_cooldown(cap_name, cap["cooldown"]):
                return cap_name
    return None
```

---

# 3. STATE MACHINE ARCHITECTURE

## System States

```
                    ┌─────────────┐
                    │   STARTUP   │
                    └──────┬──────┘
                           │ initialize()
                           ▼
                    ┌─────────────┐
        ┌──────────│   HEALTHY   │◄──────────┐
        │          └──────┬──────┘           │
        │                 │ issue_detected   │ self_heal_success
        │                 ▼                  │
        │          ┌─────────────┐           │
        │     ┌────│  DEGRADED   │───────────┘
        │     │    └──────┬──────┘
        │     │           │ critical_issue
        │     │           ▼
        │     │    ┌─────────────┐
        │     └───▶│  CRITICAL   │
        │          └──────┬──────┘
        │                 │ emergency_action
        │                 ▼
        │          ┌─────────────┐
        └──────────│  RECOVERY   │
                   └─────────────┘
```

## State Transitions

```python
class SystemState(Enum):
    STARTUP = "startup"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    RECOVERY = "recovery"

class StateManager:
    def __init__(self):
        self.state = SystemState.STARTUP
        self.transitions = {
            SystemState.STARTUP: [SystemState.HEALTHY, SystemState.DEGRADED],
            SystemState.HEALTHY: [SystemState.DEGRADED],
            SystemState.DEGRADED: [SystemState.HEALTHY, SystemState.CRITICAL],
            SystemState.CRITICAL: [SystemState.RECOVERY],
            SystemState.RECOVERY: [SystemState.HEALTHY, SystemState.DEGRADED],
        }

    def transition(self, new_state: SystemState) -> bool:
        """Attempt state transition."""
        if new_state in self.transitions.get(self.state, []):
            old_state = self.state
            self.state = new_state
            self._log_transition(old_state, new_state)
            self._trigger_state_handlers(new_state)
            return True
        return False
```

## State-Specific Behaviors

```python
STATE_BEHAVIORS = {
    SystemState.HEALTHY: {
        "check_interval": 60,
        "actions_allowed": ["all"],
        "notifications": "none"
    },
    SystemState.DEGRADED: {
        "check_interval": 30,
        "actions_allowed": ["critical", "healing"],
        "notifications": "warn"
    },
    SystemState.CRITICAL: {
        "check_interval": 15,
        "actions_allowed": ["emergency_only"],
        "notifications": "alert"
    },
    SystemState.RECOVERY: {
        "check_interval": 20,
        "actions_allowed": ["healing", "diagnosis"],
        "notifications": "info"
    }
}
```

---

# 4. PROCESS CYCLING ALGORITHMS

## Round-Robin with Priority

```python
class ProcessCycler:
    """Cycle through processes with priority awareness."""

    def __init__(self):
        self.priority_groups = {
            "critical": ["self_heal", "trading_protection"],
            "high": ["reality_check", "income_generation"],
            "medium": ["outreach", "conversion", "improvement"],
            "low": ["reporting", "cleanup"]
        }
        self.last_run = {}

    def get_next_process(self) -> str:
        """Get next process to run based on priority and recency."""

        for priority in ["critical", "high", "medium", "low"]:
            processes = self.priority_groups[priority]

            # Find process with oldest last_run
            oldest = None
            oldest_time = float('inf')

            for proc in processes:
                last = self.last_run.get(proc, 0)
                if last < oldest_time:
                    oldest_time = last
                    oldest = proc

            # Check if enough time has passed
            min_interval = self._get_min_interval(priority)
            if time.time() - oldest_time >= min_interval:
                return oldest

        return None  # All processes up to date

    def _get_min_interval(self, priority: str) -> int:
        """Minimum interval between runs by priority."""
        return {
            "critical": 15,
            "high": 60,
            "medium": 300,
            "low": 900
        }.get(priority, 60)
```

## Feedback-Driven Scheduling

```python
class FeedbackScheduler:
    """Schedule based on feedback from previous runs."""

    def __init__(self):
        self.process_stats = {}

    def record_run(self, process: str, result: dict):
        """Record process run result."""
        if process not in self.process_stats:
            self.process_stats[process] = {
                "runs": 0,
                "successes": 0,
                "failures": 0,
                "avg_duration": 0,
                "last_value": 0
            }

        stats = self.process_stats[process]
        stats["runs"] += 1

        if result.get("success"):
            stats["successes"] += 1
            stats["last_value"] = result.get("value", 0)
        else:
            stats["failures"] += 1

    def get_priority_multiplier(self, process: str) -> float:
        """Get priority multiplier based on historical performance."""
        stats = self.process_stats.get(process, {})

        # Higher success rate = higher priority
        success_rate = stats.get("successes", 0) / max(stats.get("runs", 1), 1)

        # Higher value = higher priority
        value_factor = min(stats.get("last_value", 0) / 100, 2.0)

        return success_rate * (1 + value_factor)
```

---

# 5. ACTUATOR IMPLEMENTATION DETAILS

## Actuator Hub Architecture

```python
class ActuatorHub:
    """Central hub managing all actuators."""

    def __init__(self):
        self.actuators = {}
        self.rate_limits = {}
        self.state_file = STATE_DIR / "actuator_state.json"
        self.log_file = STATE_DIR / "actuator_log.jsonl"

        self._init_actuators()

    def _init_actuators(self):
        """Initialize all available actuators."""
        # Telegram
        self.actuators["telegram"] = TelegramActuator()
        self.rate_limits["telegram"] = RateLimiter(max_calls=10, window=60)

        # Polymarket
        self.actuators["polymarket"] = PolymarketActuator()
        self.rate_limits["polymarket"] = RateLimiter(max_calls=100, window=60)

    def execute(self, actuator_name: str, action: str, params: dict) -> dict:
        """Execute action on actuator with rate limiting and logging."""

        # Check rate limit
        if not self.rate_limits[actuator_name].allow():
            return {"success": False, "error": "rate_limited"}

        # Get actuator
        actuator = self.actuators.get(actuator_name)
        if not actuator:
            return {"success": False, "error": "unknown_actuator"}

        # Execute
        try:
            method = getattr(actuator, action)
            result = method(**params)
            self._log_execution(actuator_name, action, params, result)
            return {"success": True, "result": result}
        except Exception as e:
            self._log_execution(actuator_name, action, params, {"error": str(e)})
            return {"success": False, "error": str(e)}
```

## Rate Limiter Implementation

```python
class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_calls: int, window: int):
        self.max_calls = max_calls
        self.window = window
        self.calls = []

    def allow(self) -> bool:
        """Check if call is allowed."""
        now = time.time()

        # Remove old calls
        self.calls = [t for t in self.calls if now - t < self.window]

        # Check limit
        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False

    def time_until_allowed(self) -> float:
        """Time until next call allowed."""
        if len(self.calls) < self.max_calls:
            return 0
        oldest = min(self.calls)
        return max(0, self.window - (time.time() - oldest))
```

## Polymarket Actuator Details

```python
class PolymarketActuator:
    """Execute trades on Polymarket."""

    def __init__(self):
        self.client = None
        self.safeguards = TradingSafeguards()
        self._init_client()

    def _init_client(self):
        """Initialize Polymarket client."""
        from py_clob_client.client import ClobClient

        self.client = ClobClient(
            host="https://clob.polymarket.com",
            key=os.environ.get("POLYMARKET_PRIVATE_KEY"),
            chain_id=137,
            funder=os.environ.get("POLYMARKET_FUNDER_ADDRESS")
        )

        # Derive API credentials
        creds = self.client.create_or_derive_api_creds()
        self.client.set_api_creds(creds)

    def execute_trade(self, market_id: str, side: str, amount: float, price: float) -> dict:
        """Execute trade through safeguards."""

        # Check safeguards
        check = self.safeguards.check_trade({
            "market_id": market_id,
            "side": side,
            "amount": amount,
            "price": price
        })

        if not check["allowed"]:
            return {"success": False, "reason": check["reason"]}

        # Build and submit order
        order = self.client.create_order({
            "token_id": market_id,
            "side": side.upper(),
            "size": amount,
            "price": price
        })

        result = self.client.post_order(order)
        return {"success": True, "order_id": result.get("orderID")}
```

---

# 6. TRADING SAFEGUARDS SYSTEM

## Safeguard Architecture

```python
class TradingSafeguards:
    """Multi-layer trading safeguards."""

    def __init__(self):
        self.limits = {
            "max_single_trade": 50.0,      # Max single trade
            "max_daily_volume": 500.0,     # Max daily volume
            "max_position_size": 200.0,    # Max per market
            "max_total_exposure": 500.0,   # Max total
            "min_liquidity_ratio": 0.1,    # 10% of liquidity
            "max_slippage": 0.02,          # 2% max slippage
        }
        self.daily_volume = 0
        self.positions = {}

    def check_trade(self, trade: dict) -> dict:
        """Run all safeguard checks."""
        checks = [
            self._check_size_limit,
            self._check_daily_limit,
            self._check_position_limit,
            self._check_exposure_limit,
            self._check_liquidity,
            self._check_slippage,
        ]

        for check in checks:
            result = check(trade)
            if not result["passed"]:
                return {"allowed": False, "reason": result["reason"]}

        return {"allowed": True}

    def _check_size_limit(self, trade: dict) -> dict:
        """Check single trade size limit."""
        if trade["amount"] > self.limits["max_single_trade"]:
            return {
                "passed": False,
                "reason": f"Trade size {trade['amount']} exceeds limit {self.limits['max_single_trade']}"
            }
        return {"passed": True}

    def _check_daily_limit(self, trade: dict) -> dict:
        """Check daily volume limit."""
        if self.daily_volume + trade["amount"] > self.limits["max_daily_volume"]:
            return {
                "passed": False,
                "reason": f"Would exceed daily limit. Current: {self.daily_volume}, Limit: {self.limits['max_daily_volume']}"
            }
        return {"passed": True}

    def _check_liquidity(self, trade: dict) -> dict:
        """Check liquidity is sufficient."""
        market_liquidity = self._get_market_liquidity(trade["market_id"])
        if trade["amount"] > market_liquidity * self.limits["min_liquidity_ratio"]:
            return {
                "passed": False,
                "reason": f"Trade too large relative to liquidity"
            }
        return {"passed": True}

    def _check_slippage(self, trade: dict) -> dict:
        """Check expected slippage."""
        expected_slippage = self._estimate_slippage(trade)
        if expected_slippage > self.limits["max_slippage"]:
            return {
                "passed": False,
                "reason": f"Expected slippage {expected_slippage:.2%} exceeds limit {self.limits['max_slippage']:.2%}"
            }
        return {"passed": True}
```

## Kill Switch

```python
class TradingKillSwitch:
    """Emergency kill switch for trading."""

    def __init__(self):
        self.enabled = False
        self.reason = None
        self.activated_at = None

    def activate(self, reason: str):
        """Activate kill switch - stops all trading."""
        self.enabled = True
        self.reason = reason
        self.activated_at = datetime.now()

        # Cancel all open orders
        self._cancel_all_orders()

        # Notify
        self._send_alert(f"KILL SWITCH ACTIVATED: {reason}")

    def deactivate(self, override_code: str):
        """Deactivate kill switch (requires override)."""
        if self._verify_override(override_code):
            self.enabled = False
            self.reason = None
```

---

# 7. INFRASTRUCTURE AUTO-SCALING LOGIC

## Scaling Decision Algorithm

```python
class AutoScaler:
    """Automatic infrastructure scaling."""

    def __init__(self, provisioner: AutoProvisioner):
        self.provisioner = provisioner
        self.metrics_window = 300  # 5 minutes
        self.scale_up_threshold = 80  # 80% utilization
        self.scale_down_threshold = 20  # 20% utilization
        self.cooldown = 600  # 10 minutes between scaling

    def evaluate(self) -> ScalingDecision:
        """Evaluate if scaling needed."""
        metrics = self._collect_metrics()

        # Calculate utilization
        cpu_util = metrics["cpu_percent"]
        mem_util = metrics["memory_percent"]
        avg_util = (cpu_util + mem_util) / 2

        # Check scale up
        if avg_util > self.scale_up_threshold:
            if self._can_scale("up"):
                return ScalingDecision(
                    action="scale_up",
                    reason=f"Utilization at {avg_util:.1f}%",
                    target_size=self._calculate_target_size("up")
                )

        # Check scale down
        if avg_util < self.scale_down_threshold:
            if self._can_scale("down"):
                return ScalingDecision(
                    action="scale_down",
                    reason=f"Utilization at {avg_util:.1f}%",
                    target_size=self._calculate_target_size("down")
                )

        return ScalingDecision(action="none")

    def _calculate_target_size(self, direction: str) -> str:
        """Calculate target instance size."""
        current = self._get_current_size()
        sizes = ["s-1vcpu-1gb", "s-1vcpu-2gb", "s-2vcpu-2gb", "s-2vcpu-4gb"]

        current_idx = sizes.index(current) if current in sizes else 0

        if direction == "up":
            return sizes[min(current_idx + 1, len(sizes) - 1)]
        else:
            return sizes[max(current_idx - 1, 0)]
```

## Predictive Scaling

```python
class PredictiveScaler:
    """Scale based on predicted demand."""

    def __init__(self):
        self.history = []
        self.prediction_window = 3600  # 1 hour ahead

    def predict_demand(self) -> float:
        """Predict demand for next hour."""
        if len(self.history) < 10:
            return None

        # Simple moving average prediction
        recent = self.history[-10:]
        trend = (recent[-1] - recent[0]) / len(recent)
        predicted = recent[-1] + trend * (self.prediction_window / 300)

        return max(0, predicted)

    def should_preemptive_scale(self) -> bool:
        """Check if should scale preemptively."""
        predicted = self.predict_demand()
        if predicted is None:
            return False

        current_capacity = self._get_current_capacity()
        return predicted > current_capacity * 0.9
```

---

# 8. HARDWARE DECISION ENGINE

## Decision Tree

```python
class HardwareDecisionEngine:
    """Make hardware-related decisions."""

    def decide(self, metrics: HardwareMetrics) -> HardwareDecision:
        """Decision tree for hardware actions."""

        # Critical checks first
        if metrics.disk_percent > 95:
            return HardwareDecision(
                action="emergency_cleanup",
                priority="critical",
                reason="Disk almost full"
            )

        if metrics.memory_percent > 95:
            return HardwareDecision(
                action="kill_non_essential",
                priority="critical",
                reason="Memory almost full"
            )

        # Degraded checks
        if metrics.cpu_percent > 90:
            return HardwareDecision(
                action="scale_up",
                priority="high",
                reason="CPU overloaded"
            )

        if metrics.network_errors > 100:
            return HardwareDecision(
                action="network_diagnosis",
                priority="high",
                reason="Network errors detected"
            )

        # Optimization checks
        if metrics.cpu_percent < 10 and metrics.memory_percent < 30:
            return HardwareDecision(
                action="consider_scale_down",
                priority="low",
                reason="Resources underutilized"
            )

        return HardwareDecision(action="none")
```

## Trading Protection Priority

```python
class TradingProtectionManager:
    """Protect trading capability above all else."""

    TRADING_PROCESSES = [
        "polymarket_live",
        "trade_executor",
        "signal_generator",
        "trading_brain"
    ]

    def is_trading_process(self, process: str) -> bool:
        """Check if process is trading-related."""
        return any(tp in process for tp in self.TRADING_PROCESSES)

    def protect_trading(self, action: HardwareDecision) -> HardwareDecision:
        """Modify decision to protect trading."""

        if action.action == "kill_non_essential":
            # Never kill trading processes
            action.exclude = self.TRADING_PROCESSES

        if action.action == "scale_down":
            # Check if trading would be impacted
            if self._trading_would_be_impacted():
                action.action = "none"
                action.reason = "Scale down blocked - trading protection"

        return action
```

---

# 9. SELF-HEALING ALGORITHMS

## Issue Detection

```python
class IssueDetector:
    """Detect system issues."""

    def scan(self) -> List[Issue]:
        """Scan for all issues."""
        issues = []

        # Process checks
        issues.extend(self._check_processes())

        # State checks
        issues.extend(self._check_state_files())

        # Resource checks
        issues.extend(self._check_resources())

        # Connectivity checks
        issues.extend(self._check_connectivity())

        return issues

    def _check_processes(self) -> List[Issue]:
        """Check for process issues."""
        issues = []

        expected_processes = [
            "evolution_engine",
            "master_orchestrator",
            "polymarket_live"
        ]

        for proc in expected_processes:
            if not self._is_process_running(proc):
                issues.append(Issue(
                    type="process_down",
                    severity="high",
                    target=proc,
                    auto_fixable=True
                ))

        return issues

    def _check_state_files(self) -> List[Issue]:
        """Check state file health."""
        issues = []

        for state_file in STATE_DIR.glob("*.json"):
            try:
                data = json.loads(state_file.read_text())
                # Check freshness
                if "timestamp" in data:
                    age = time.time() - parse_timestamp(data["timestamp"])
                    if age > 3600:  # 1 hour stale
                        issues.append(Issue(
                            type="stale_state",
                            severity="medium",
                            target=str(state_file),
                            auto_fixable=False
                        ))
            except json.JSONDecodeError:
                issues.append(Issue(
                    type="corrupt_state",
                    severity="high",
                    target=str(state_file),
                    auto_fixable=True
                ))

        return issues
```

## Auto-Fix Implementation

```python
class AutoFixer:
    """Automatically fix detected issues."""

    FIX_HANDLERS = {
        "process_down": "_fix_process_down",
        "corrupt_state": "_fix_corrupt_state",
        "disk_full": "_fix_disk_full",
        "memory_high": "_fix_memory_high",
        "connectivity_lost": "_fix_connectivity",
    }

    def fix(self, issue: Issue) -> FixResult:
        """Attempt to fix issue."""
        if not issue.auto_fixable:
            return FixResult(success=False, reason="Not auto-fixable")

        handler_name = self.FIX_HANDLERS.get(issue.type)
        if not handler_name:
            return FixResult(success=False, reason="No handler")

        handler = getattr(self, handler_name)
        return handler(issue)

    def _fix_process_down(self, issue: Issue) -> FixResult:
        """Restart down process."""
        try:
            subprocess.Popen(
                ["python3", f"autonomous/{issue.target}.py"],
                cwd="/root/hands-off-engine",
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return FixResult(success=True, action="restarted")
        except Exception as e:
            return FixResult(success=False, reason=str(e))

    def _fix_corrupt_state(self, issue: Issue) -> FixResult:
        """Restore corrupt state from backup."""
        backup_path = Path(issue.target).with_suffix(".json.bak")
        if backup_path.exists():
            shutil.copy(backup_path, issue.target)
            return FixResult(success=True, action="restored_from_backup")
        else:
            # Initialize empty state
            Path(issue.target).write_text("{}")
            return FixResult(success=True, action="initialized_empty")

    def _fix_disk_full(self, issue: Issue) -> FixResult:
        """Clean up disk space."""
        cleaned = 0

        # Clean old logs
        for log in Path("/root/hands-off-engine/logs").glob("*.log"):
            if log.stat().st_mtime < time.time() - 604800:  # 1 week
                log.unlink()
                cleaned += log.stat().st_size

        # Clean pycache
        for pycache in Path("/root/hands-off-engine").rglob("__pycache__"):
            shutil.rmtree(pycache, ignore_errors=True)

        return FixResult(success=True, action=f"cleaned_{cleaned}_bytes")
```

---

# 10. MULTI-AGENT COORDINATION

## Peanut Gallery Architecture

```python
class PeanutGallery:
    """Multiple perspectives watching and commenting."""

    OBSERVERS = {
        "skeptic": {
            "personality": "Critical, questions everything",
            "focus": "risks, flaws, doubts",
            "prompt_style": "What could go wrong with...?"
        },
        "optimist": {
            "personality": "Positive, sees potential",
            "focus": "opportunities, upside",
            "prompt_style": "What's great about...?"
        },
        "pragmatist": {
            "personality": "Practical, action-oriented",
            "focus": "implementation, next steps",
            "prompt_style": "What should we do about...?"
        },
        "contrarian": {
            "personality": "Opposite viewpoint",
            "focus": "alternative approaches",
            "prompt_style": "What if we did the opposite of...?"
        },
        "historian": {
            "personality": "Pattern recognition",
            "focus": "past experiences, patterns",
            "prompt_style": "When did we see this before...?"
        },
        "numbers": {
            "personality": "Data-driven",
            "focus": "metrics, evidence",
            "prompt_style": "What does the data say about...?"
        }
    }

    def gather_perspectives(self, topic: str) -> List[Perspective]:
        """Gather perspectives from all observers."""
        perspectives = []

        for name, config in self.OBSERVERS.items():
            perspective = self._get_perspective(name, config, topic)
            perspectives.append(perspective)

        return perspectives

    def synthesize_consensus(self, perspectives: List[Perspective]) -> Consensus:
        """Find consensus among perspectives."""
        # Weight perspectives
        weights = {
            "pragmatist": 1.5,  # Action-oriented gets more weight
            "numbers": 1.3,    # Data-driven
            "skeptic": 1.0,
            "optimist": 0.8,
            "contrarian": 0.5,
            "historian": 1.0
        }

        weighted_scores = {}
        for p in perspectives:
            weight = weights.get(p.observer, 1.0)
            for action, score in p.action_scores.items():
                if action not in weighted_scores:
                    weighted_scores[action] = 0
                weighted_scores[action] += score * weight

        # Find consensus action
        best_action = max(weighted_scores, key=weighted_scores.get)

        return Consensus(
            action=best_action,
            confidence=weighted_scores[best_action] / sum(weighted_scores.values()),
            perspectives=perspectives
        )
```

## Coordination Agent

```python
class CoordinationAgent:
    """Coordinate between all agents."""

    def __init__(self):
        self.agents = {}
        self.message_bus = MessageBus()

    def register_agent(self, name: str, agent: Any):
        """Register an agent."""
        self.agents[name] = agent
        self.message_bus.subscribe(name)

    def broadcast(self, message: Message):
        """Broadcast message to all agents."""
        for name in self.agents:
            self.message_bus.send(name, message)

    def request_consensus(self, topic: str) -> ConsensusResult:
        """Request consensus from all agents."""
        responses = {}

        for name, agent in self.agents.items():
            if hasattr(agent, "vote"):
                responses[name] = agent.vote(topic)

        return self._calculate_consensus(responses)

    def _calculate_consensus(self, responses: Dict) -> ConsensusResult:
        """Calculate consensus from responses."""
        votes = {}
        for agent, response in responses.items():
            vote = response.get("vote")
            if vote not in votes:
                votes[vote] = []
            votes[vote].append(agent)

        # Find majority
        majority_vote = max(votes, key=lambda v: len(votes[v]))
        majority_size = len(votes[majority_vote])
        total_votes = sum(len(v) for v in votes.values())

        return ConsensusResult(
            decision=majority_vote,
            confidence=majority_size / total_votes,
            votes=votes
        )
```

---

# 11. SIGNAL GENERATION PIPELINE

## Pipeline Architecture

```
Market Data → Filters → Feature Extraction → Model → Signals → Ranking → Output
```

## Signal Generator Implementation

```python
class SignalGenerator:
    """Generate trading signals."""

    def __init__(self):
        self.filters = [
            LiquidityFilter(min_volume=1000),
            TimeToResolutionFilter(min_days=1, max_days=90),
            SpreadFilter(max_spread=0.10),
        ]
        self.models = [
            EdgeDetector(),
            MomentumScorer(),
            SharpTrackerSignals(),
        ]

    def generate(self, markets: List[Market]) -> List[Signal]:
        """Generate signals for markets."""
        signals = []

        for market in markets:
            # Apply filters
            if not self._passes_filters(market):
                continue

            # Extract features
            features = self._extract_features(market)

            # Run models
            model_signals = []
            for model in self.models:
                signal = model.predict(market, features)
                if signal:
                    model_signals.append(signal)

            # Combine signals
            if model_signals:
                combined = self._combine_signals(model_signals)
                signals.append(combined)

        # Rank signals
        signals.sort(key=lambda s: s.score, reverse=True)

        return signals[:10]  # Top 10

    def _extract_features(self, market: Market) -> Dict:
        """Extract features from market."""
        return {
            "price": market.yes_price,
            "volume_24h": market.volume_24h,
            "liquidity": market.liquidity,
            "time_to_resolution": market.time_to_resolution,
            "price_change_24h": market.price_change_24h,
            "sharp_wallet_flow": self._get_sharp_flow(market),
        }

    def _combine_signals(self, signals: List[Signal]) -> Signal:
        """Combine multiple model signals."""
        # Weighted average
        total_weight = sum(s.confidence for s in signals)
        combined_score = sum(s.score * s.confidence for s in signals) / total_weight

        return Signal(
            market_id=signals[0].market_id,
            direction=signals[0].direction,
            score=combined_score,
            confidence=total_weight / len(signals),
            sources=[s.source for s in signals]
        )
```

## Edge Detection

```python
class EdgeDetector:
    """Detect trading edge opportunities."""

    def predict(self, market: Market, features: Dict) -> Optional[Signal]:
        """Detect if there's edge in market."""

        # Calculate implied probability
        implied_prob = market.yes_price

        # Estimate true probability (using various inputs)
        estimated_prob = self._estimate_probability(market, features)

        # Calculate edge
        edge = estimated_prob - implied_prob

        # Only signal if edge is significant
        if abs(edge) < 0.05:  # 5% minimum edge
            return None

        direction = "BUY" if edge > 0 else "SELL"
        score = abs(edge) * features.get("liquidity", 1) / 1000

        return Signal(
            market_id=market.id,
            direction=direction,
            score=score,
            confidence=0.7,
            source="edge_detector",
            metadata={"edge": edge, "estimated_prob": estimated_prob}
        )
```

---

# 12. POSITION SIZING MATHEMATICS

## Kelly Criterion Implementation

```python
def kelly_criterion(win_prob: float, win_return: float, loss_return: float = -1.0) -> float:
    """
    Calculate Kelly optimal bet fraction.

    f* = (p * b - q) / b

    Where:
    - p = probability of winning
    - q = probability of losing (1 - p)
    - b = ratio of win to loss
    """
    if win_prob <= 0 or win_prob >= 1:
        return 0.0

    q = 1 - win_prob
    b = abs(win_return / loss_return)

    kelly = (win_prob * b - q) / b

    return max(0, kelly)


def half_kelly(win_prob: float, win_return: float, loss_return: float = -1.0) -> float:
    """Half Kelly for reduced variance."""
    return kelly_criterion(win_prob, win_return, loss_return) / 2


def fractional_kelly(win_prob: float, win_return: float, fraction: float = 0.25) -> float:
    """Fractional Kelly (commonly 1/4 Kelly)."""
    return kelly_criterion(win_prob, win_return) * fraction
```

## Position Sizing Algorithm

```python
class PositionSizer:
    """Calculate optimal position sizes."""

    def __init__(self, bankroll: float, max_position_pct: float = 0.10):
        self.bankroll = bankroll
        self.max_position_pct = max_position_pct

    def calculate_size(self, signal: Signal, current_positions: Dict) -> float:
        """Calculate position size for signal."""

        # Kelly-based size
        kelly_size = self._kelly_size(signal)

        # Apply maximum constraint
        max_size = self.bankroll * self.max_position_pct

        # Apply liquidity constraint
        liquidity_size = signal.market_liquidity * 0.05  # Max 5% of liquidity

        # Apply correlation constraint
        correlation_adjusted = self._adjust_for_correlation(kelly_size, current_positions)

        # Take minimum of all constraints
        size = min(kelly_size, max_size, liquidity_size, correlation_adjusted)

        # Round to valid increment
        return round(size, 2)

    def _kelly_size(self, signal: Signal) -> float:
        """Calculate Kelly-based size."""
        edge = signal.metadata.get("edge", 0)
        confidence = signal.confidence

        # Adjust win probability by confidence
        adjusted_prob = 0.5 + (edge * confidence)

        # Win return is 1/price - 1
        price = signal.metadata.get("price", 0.5)
        win_return = (1 / price) - 1 if price > 0 else 0

        # Use 1/4 Kelly for safety
        fraction = fractional_kelly(adjusted_prob, win_return, 0.25)

        return self.bankroll * fraction

    def _adjust_for_correlation(self, size: float, positions: Dict) -> float:
        """Reduce size if correlated with existing positions."""
        # Simple correlation check based on market category
        correlation_factor = 1.0

        for pos_id, pos_data in positions.items():
            if self._are_correlated(pos_id, signal.market_id):
                correlation_factor *= 0.8  # Reduce by 20% per correlation

        return size * max(0.5, correlation_factor)
```

---

# 13. COST OPTIMIZATION ALGORITHMS

## AI Cost Optimization

```python
class AICostOptimizer:
    """Optimize AI API costs."""

    def __init__(self):
        self.cost_history = []
        self.budget_daily = 10.0  # $10/day

    def should_call_ai(self, context: Dict) -> bool:
        """Determine if AI call is worth the cost."""
        estimated_cost = self._estimate_cost(context)
        expected_value = self._estimate_value(context)

        # Only call if EV > cost with margin
        return expected_value > estimated_cost * 1.5

    def _estimate_cost(self, context: Dict) -> float:
        """Estimate cost of AI call."""
        # Token estimation
        input_tokens = len(context.get("prompt", "")) / 4
        output_tokens = context.get("max_output", 500)

        # Cost per token (approximate)
        input_cost = input_tokens * 0.000003  # $3/1M input tokens
        output_cost = output_tokens * 0.000015  # $15/1M output tokens

        return input_cost + output_cost

    def _estimate_value(self, context: Dict) -> float:
        """Estimate value of AI response."""
        task_type = context.get("task_type")

        value_map = {
            "trading_signal": 1.0,  # High value
            "content_generation": 0.5,
            "analysis": 0.3,
            "formatting": 0.1,  # Low value - maybe don't use AI
        }

        base_value = value_map.get(task_type, 0.2)

        # Adjust by urgency
        if context.get("urgent"):
            base_value *= 2

        return base_value

    def select_provider(self, task: Dict) -> str:
        """Select cheapest provider for task."""
        providers = {
            "claude": {"cost_per_1k": 0.015, "quality": 0.95},
            "gpt4": {"cost_per_1k": 0.03, "quality": 0.90},
            "gpt35": {"cost_per_1k": 0.002, "quality": 0.70},
            "local": {"cost_per_1k": 0.0, "quality": 0.50},
        }

        min_quality = task.get("min_quality", 0.6)

        # Filter by quality
        eligible = {k: v for k, v in providers.items() if v["quality"] >= min_quality}

        # Select cheapest
        return min(eligible, key=lambda k: eligible[k]["cost_per_1k"])
```

## Infrastructure Cost Optimization

```python
class InfraCostOptimizer:
    """Optimize infrastructure costs."""

    def __init__(self):
        self.hourly_costs = {}

    def recommend_optimization(self, usage: Dict) -> List[Recommendation]:
        """Recommend cost optimizations."""
        recommendations = []

        # Check for underutilized instances
        for instance_id, metrics in usage.items():
            if metrics["cpu_avg"] < 10 and metrics["memory_avg"] < 30:
                recommendations.append(Recommendation(
                    action="downsize",
                    target=instance_id,
                    estimated_savings=self._calculate_downsize_savings(instance_id)
                ))

        # Check for spot instance candidates
        for instance_id, metrics in usage.items():
            if metrics.get("interruptible", True):
                recommendations.append(Recommendation(
                    action="convert_to_spot",
                    target=instance_id,
                    estimated_savings=self._calculate_spot_savings(instance_id)
                ))

        # Check for reserved instance opportunities
        if self._stable_usage_detected(usage):
            recommendations.append(Recommendation(
                action="purchase_reserved",
                estimated_savings=self._calculate_reserved_savings()
            ))

        return recommendations
```

---

# 14. STATE SYNCHRONIZATION PROTOCOL

## Sync Algorithm

```python
class StateSync:
    """Synchronize state across components."""

    def __init__(self):
        self.state_versions = {}
        self.sync_log = STATE_DIR / "sync_log.jsonl"

    def sync(self) -> SyncResult:
        """Perform full state synchronization."""
        issues = []

        # 1. Validate all state files
        validation_issues = self._validate_all()
        issues.extend(validation_issues)

        # 2. Check consistency across files
        consistency_issues = self._check_consistency()
        issues.extend(consistency_issues)

        # 3. Resolve conflicts
        for issue in issues:
            if issue.resolvable:
                self._resolve(issue)

        # 4. Update versions
        self._update_versions()

        return SyncResult(
            success=len(issues) == 0,
            issues=issues,
            resolved=len([i for i in issues if i.resolved])
        )

    def _check_consistency(self) -> List[Issue]:
        """Check consistency between related state files."""
        issues = []

        # Check CURRENT_TRUTH vs individual states
        current = self._read_json(STATE_DIR / "CURRENT_TRUTH.json")

        if current:
            # Financial consistency
            trading_state = self._read_json(STATE_DIR / "trading_status.json")
            if trading_state:
                if current.get("financial", {}).get("positions") != trading_state.get("total_value"):
                    issues.append(Issue(
                        type="inconsistency",
                        files=["CURRENT_TRUTH.json", "trading_status.json"],
                        field="positions",
                        resolvable=True
                    ))

        return issues

    def _resolve(self, issue: Issue):
        """Resolve a consistency issue."""
        if issue.type == "inconsistency":
            # Take most recent as truth
            timestamps = {}
            for file in issue.files:
                data = self._read_json(STATE_DIR / file)
                timestamps[file] = data.get("timestamp", "")

            source = max(timestamps, key=timestamps.get)
            self._propagate_value(source, issue.files, issue.field)
            issue.resolved = True
```

## Version Control

```python
class StateVersionControl:
    """Version control for state files."""

    def __init__(self):
        self.versions = STATE_DIR / "state_versions.json"

    def checkpoint(self, description: str) -> str:
        """Create state checkpoint."""
        checkpoint_id = f"cp_{int(time.time())}"

        # Create checkpoint directory
        checkpoint_dir = STATE_DIR / "checkpoints" / checkpoint_id
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Copy all state files
        for state_file in STATE_DIR.glob("*.json"):
            shutil.copy(state_file, checkpoint_dir)

        # Record checkpoint
        self._record_checkpoint(checkpoint_id, description)

        return checkpoint_id

    def restore(self, checkpoint_id: str) -> bool:
        """Restore from checkpoint."""
        checkpoint_dir = STATE_DIR / "checkpoints" / checkpoint_id

        if not checkpoint_dir.exists():
            return False

        # Restore all files
        for state_file in checkpoint_dir.glob("*.json"):
            shutil.copy(state_file, STATE_DIR)

        return True

    def diff(self, checkpoint_id: str) -> Dict:
        """Show diff from checkpoint."""
        checkpoint_dir = STATE_DIR / "checkpoints" / checkpoint_id
        diffs = {}

        for current_file in STATE_DIR.glob("*.json"):
            checkpoint_file = checkpoint_dir / current_file.name
            if checkpoint_file.exists():
                current = json.loads(current_file.read_text())
                checkpoint = json.loads(checkpoint_file.read_text())
                if current != checkpoint:
                    diffs[current_file.name] = self._compute_diff(checkpoint, current)

        return diffs
```

---

# 15. FEEDBACK LOOP MECHANICS

## Feedback Collection

```python
class FeedbackCollector:
    """Collect feedback from all actions."""

    def collect(self, action: Action, result: Result) -> Feedback:
        """Collect feedback from action result."""
        feedback = Feedback(
            action_id=action.id,
            action_type=action.type,
            timestamp=datetime.now().isoformat(),
            success=result.success,
            metrics={}
        )

        # Collect specific metrics based on action type
        if action.type == "trading":
            feedback.metrics = {
                "pnl": result.data.get("pnl", 0),
                "fill_rate": result.data.get("fill_rate", 0),
                "slippage": result.data.get("slippage", 0),
            }
        elif action.type == "outreach":
            feedback.metrics = {
                "responses": result.data.get("responses", 0),
                "conversions": result.data.get("conversions", 0),
            }

        return feedback

    def aggregate(self, feedbacks: List[Feedback]) -> AggregatedFeedback:
        """Aggregate feedback over time window."""
        by_type = {}

        for fb in feedbacks:
            if fb.action_type not in by_type:
                by_type[fb.action_type] = []
            by_type[fb.action_type].append(fb)

        aggregated = {}
        for action_type, fbs in by_type.items():
            aggregated[action_type] = {
                "count": len(fbs),
                "success_rate": sum(1 for f in fbs if f.success) / len(fbs),
                "avg_metrics": self._average_metrics(fbs)
            }

        return AggregatedFeedback(data=aggregated)
```

## Learning from Feedback

```python
class FeedbackLearner:
    """Learn from feedback to improve decisions."""

    def __init__(self):
        self.model_weights = {}

    def learn(self, feedback: AggregatedFeedback):
        """Update internal models based on feedback."""
        for action_type, data in feedback.data.items():
            success_rate = data["success_rate"]

            # Update action weight
            current_weight = self.model_weights.get(action_type, 1.0)
            # Exponential moving average
            new_weight = current_weight * 0.9 + success_rate * 0.1
            self.model_weights[action_type] = new_weight

    def get_action_weight(self, action_type: str) -> float:
        """Get learned weight for action type."""
        return self.model_weights.get(action_type, 1.0)

    def recommend_adjustments(self) -> List[Adjustment]:
        """Recommend adjustments based on learning."""
        adjustments = []

        for action_type, weight in self.model_weights.items():
            if weight < 0.3:
                adjustments.append(Adjustment(
                    action_type=action_type,
                    recommendation="reduce_frequency",
                    reason=f"Low success rate (weight: {weight:.2f})"
                ))
            elif weight > 0.8:
                adjustments.append(Adjustment(
                    action_type=action_type,
                    recommendation="increase_frequency",
                    reason=f"High success rate (weight: {weight:.2f})"
                ))

        return adjustments
```

---

# 16. APPROVAL QUEUE SYSTEM

## Queue Implementation

```python
class ApprovalQueue:
    """Queue for human approval of risky actions."""

    def __init__(self):
        self.queue_file = STATE_DIR / "approval_queue.json"
        self.queue = self._load_queue()

    def submit(self, action: Action, reason: str) -> str:
        """Submit action for approval."""
        request_id = f"req_{int(time.time())}_{random.randint(1000, 9999)}"

        request = {
            "id": request_id,
            "action": action.to_dict(),
            "reason": reason,
            "submitted_at": datetime.now().isoformat(),
            "status": "pending",
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }

        self.queue.append(request)
        self._save_queue()
        self._notify_pending(request)

        return request_id

    def check_status(self, request_id: str) -> str:
        """Check approval status."""
        for request in self.queue:
            if request["id"] == request_id:
                return request["status"]
        return "not_found"

    def approve(self, request_id: str, approver: str) -> bool:
        """Approve a request."""
        for request in self.queue:
            if request["id"] == request_id:
                request["status"] = "approved"
                request["approved_by"] = approver
                request["approved_at"] = datetime.now().isoformat()
                self._save_queue()
                return True
        return False

    def reject(self, request_id: str, reason: str) -> bool:
        """Reject a request."""
        for request in self.queue:
            if request["id"] == request_id:
                request["status"] = "rejected"
                request["rejection_reason"] = reason
                request["rejected_at"] = datetime.now().isoformat()
                self._save_queue()
                return True
        return False
```

## Auto-Approval Logic

```python
class AutoApprover:
    """Automatically approve low-risk actions."""

    AUTO_APPROVE_THRESHOLDS = {
        "max_cost": 50.0,           # Auto-approve if cost < $50
        "max_risk_score": 0.3,      # Auto-approve if risk < 30%
        "min_success_history": 0.8, # Auto-approve if 80%+ historical success
    }

    def can_auto_approve(self, action: Action) -> Tuple[bool, str]:
        """Check if action can be auto-approved."""

        # Check cost
        if action.estimated_cost > self.AUTO_APPROVE_THRESHOLDS["max_cost"]:
            return False, f"Cost {action.estimated_cost} exceeds threshold"

        # Check risk
        if action.risk_score > self.AUTO_APPROVE_THRESHOLDS["max_risk_score"]:
            return False, f"Risk {action.risk_score} exceeds threshold"

        # Check history
        historical_success = self._get_historical_success(action.type)
        if historical_success < self.AUTO_APPROVE_THRESHOLDS["min_success_history"]:
            return False, f"Historical success {historical_success:.0%} below threshold"

        return True, "All thresholds passed"
```

---

# 17. EDGE CASES & FAILURE MODES

## Known Edge Cases

### Stale State Files
```python
Problem: State file not updated for extended period
Detection: Check timestamp vs current time
Handling:
  1. Mark state as stale
  2. Attempt to refresh from source
  3. If unable, use fallback values
  4. Alert if critical state
```

### Circular Dependencies
```python
Problem: Process A waits for B, B waits for A
Detection: Track waiting relationships
Handling:
  1. Detect cycle
  2. Break cycle by resetting one process
  3. Log for debugging
```

### API Rate Limits
```python
Problem: External API returns 429 Too Many Requests
Detection: Check response code
Handling:
  1. Back off exponentially
  2. Queue pending requests
  3. Switch to fallback if available
```

### Partial Failures
```python
Problem: Multi-step operation fails midway
Detection: Transaction logging
Handling:
  1. Detect incomplete transaction
  2. Attempt rollback
  3. If rollback fails, mark for manual review
```

## Failure Mode Handling

```python
class FailureHandler:
    """Handle various failure modes."""

    HANDLERS = {
        "process_crash": "_handle_process_crash",
        "state_corruption": "_handle_state_corruption",
        "api_failure": "_handle_api_failure",
        "disk_full": "_handle_disk_full",
        "memory_exhausted": "_handle_memory_exhausted",
        "network_failure": "_handle_network_failure",
    }

    def handle(self, failure: Failure) -> bool:
        """Handle a failure."""
        handler_name = self.HANDLERS.get(failure.type)
        if not handler_name:
            return self._handle_unknown(failure)

        handler = getattr(self, handler_name)
        return handler(failure)

    def _handle_process_crash(self, failure: Failure) -> bool:
        """Handle crashed process."""
        # 1. Check if critical
        if self._is_critical_process(failure.process):
            # Immediate restart
            return self._restart_process(failure.process)
        else:
            # Queue for restart
            self._queue_restart(failure.process)
            return True

    def _handle_unknown(self, failure: Failure) -> bool:
        """Handle unknown failure type."""
        # Log everything
        self._log_failure(failure)
        # Notify
        self._notify_failure(failure)
        # Don't claim success
        return False
```

---

# 18. PERFORMANCE OPTIMIZATION

## Caching Strategy

```python
class StateCache:
    """Cache frequently accessed state."""

    def __init__(self, max_age: int = 60):
        self.cache = {}
        self.max_age = max_age

    def get(self, key: str) -> Optional[Any]:
        """Get cached value if fresh."""
        entry = self.cache.get(key)
        if entry:
            if time.time() - entry["timestamp"] < self.max_age:
                return entry["value"]
        return None

    def set(self, key: str, value: Any):
        """Cache a value."""
        self.cache[key] = {
            "value": value,
            "timestamp": time.time()
        }

    def invalidate(self, key: str):
        """Invalidate cached value."""
        if key in self.cache:
            del self.cache[key]
```

## Batch Operations

```python
class BatchProcessor:
    """Process operations in batches."""

    def __init__(self, batch_size: int = 10, flush_interval: int = 5):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.pending = []
        self.last_flush = time.time()

    def add(self, operation: Any):
        """Add operation to batch."""
        self.pending.append(operation)

        if len(self.pending) >= self.batch_size:
            self.flush()
        elif time.time() - self.last_flush >= self.flush_interval:
            self.flush()

    def flush(self):
        """Flush pending operations."""
        if not self.pending:
            return

        # Process all pending in single batch
        self._process_batch(self.pending)
        self.pending = []
        self.last_flush = time.time()
```

---

# 19. SECURITY IMPLEMENTATION

## Credential Protection

```python
class CredentialManager:
    """Manage credentials securely."""

    def __init__(self):
        self.env_files = [
            ".env",
            ".env.polymarket",
        ]

    def load_credential(self, name: str) -> Optional[str]:
        """Load credential from environment."""
        # Try environment first
        value = os.environ.get(name)
        if value:
            return value

        # Try .env files
        for env_file in self.env_files:
            value = self._load_from_file(env_file, name)
            if value:
                return value

        return None

    def rotate_credential(self, name: str, new_value: str):
        """Rotate a credential."""
        # 1. Backup old value
        old_value = self.load_credential(name)
        self._backup_credential(name, old_value)

        # 2. Update credential
        self._update_credential(name, new_value)

        # 3. Verify new credential works
        if not self._verify_credential(name, new_value):
            # Rollback
            self._update_credential(name, old_value)
            raise CredentialRotationError(f"New credential for {name} failed verification")
```

## Input Validation

```python
class InputValidator:
    """Validate all external inputs."""

    def validate_trade(self, trade: Dict) -> ValidationResult:
        """Validate trade parameters."""
        errors = []

        # Market ID
        if not trade.get("market_id"):
            errors.append("market_id required")
        elif not self._is_valid_market_id(trade["market_id"]):
            errors.append("invalid market_id format")

        # Side
        if trade.get("side") not in ["BUY", "SELL"]:
            errors.append("side must be BUY or SELL")

        # Amount
        amount = trade.get("amount", 0)
        if amount <= 0:
            errors.append("amount must be positive")
        elif amount > 1000:
            errors.append("amount exceeds maximum")

        # Price
        price = trade.get("price", 0)
        if price <= 0 or price >= 1:
            errors.append("price must be between 0 and 1")

        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors
        )
```

---

# 20. SYSTEM EVOLUTION PATTERNS

## Self-Modification

```python
class SelfModifier:
    """System can modify itself."""

    ALLOWED_MODIFICATIONS = [
        "add_capability",
        "modify_threshold",
        "add_endpoint",
        "update_schedule",
    ]

    def modify(self, modification: Modification) -> bool:
        """Apply self-modification."""
        if modification.type not in self.ALLOWED_MODIFICATIONS:
            return False

        # 1. Validate modification
        if not self._validate(modification):
            return False

        # 2. Backup current state
        self._backup_before_modify()

        # 3. Apply modification
        try:
            self._apply(modification)
        except Exception as e:
            self._rollback()
            return False

        # 4. Verify system still works
        if not self._verify_system():
            self._rollback()
            return False

        # 5. Record modification
        self._record(modification)

        return True
```

## Evolution Tracking

```python
class EvolutionTracker:
    """Track system evolution over time."""

    def __init__(self):
        self.evolution_log = STATE_DIR / "evolution_history.jsonl"

    def record_evolution(self, change: Change):
        """Record evolutionary change."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": change.type,
            "description": change.description,
            "metrics_before": change.metrics_before,
            "metrics_after": change.metrics_after,
            "improvement": self._calculate_improvement(
                change.metrics_before,
                change.metrics_after
            )
        }

        with open(self.evolution_log, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_evolution_summary(self) -> Dict:
        """Summarize evolution history."""
        entries = self._read_log()

        return {
            "total_changes": len(entries),
            "improvements": sum(1 for e in entries if e.get("improvement", 0) > 0),
            "regressions": sum(1 for e in entries if e.get("improvement", 0) < 0),
            "avg_improvement": sum(e.get("improvement", 0) for e in entries) / max(len(entries), 1)
        }
```

---

# APPENDIX: ALGORITHM COMPLEXITY

| Algorithm | Time Complexity | Space Complexity |
|-----------|----------------|------------------|
| Decision Selection | O(n log n) | O(n) |
| Process Cycling | O(n) | O(1) |
| State Sync | O(n*m) | O(n) |
| Signal Generation | O(n*k) | O(n) |
| Position Sizing | O(n) | O(1) |
| Self-Healing Scan | O(n) | O(n) |
| Feedback Aggregation | O(n) | O(k) |

Where:
- n = number of items/markets
- m = number of state files
- k = number of models/categories

---

*This advanced documentation covers deep technical internals. Implementation details may evolve - always reference source code for current behavior.*
