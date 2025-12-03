# Spark Plug v0.5: Per-Kernel History Policy Specification

**Status**: Draft
**Version**: 0.5
**Date**: 2025-11-26
**Depends On**: Spark Plug v0.4 (AI Runner Integration)

---

## Executive Summary

Currently, all kernels receive the same history treatment: max 50 events, no importance filtering, no kind/tag filtering. This specification adds **per-kernel history policies** that allow each kernel to specify:

- **Event kind filtering** (e.g., risk_model_v2 focuses on `risk_decision` events)
- **Importance thresholds** (e.g., trading_philosophy wants importance >= 7)
- **Tag filtering** (e.g., only events tagged with `lesson`)
- **Time windows** (e.g., last 7 days vs 30 days)
- **Max events** (per-kernel limits)

This makes Spark Plug much smarter about feeding relevant history to each kernel.

---

## Motivation & Use Cases

### Current Limitation
```python
# All kernels get the same treatment
events = load_kernel_history_events('risk_model_v2', max_events=50)
events = load_kernel_history_events('trading_philosophy', max_events=50)
# No filtering by importance, kind, tags, or time window
```

### Desired Behavior

**Use Case 1: risk_model_v2**
- Focus on `risk_decision` and `decider_outcome` events
- Last 7 days only (recent risk calibration)
- Importance >= 6 (filter out low-priority events)
- Max 100 events

**Use Case 2: trading_philosophy**
- Focus on `lesson` and `manual_override` events
- Last 30 days (longer learning window)
- Importance >= 7 (only significant lessons)
- Max 50 events

**Use Case 3: system_health**
- Focus on `system_error` and `health_check` events
- Last 24 hours (recent health status)
- All importance levels
- Max 200 events

---

## Design Overview

### 1. Config Schema

**File**: `ai/config/sparkplug_history_policies.json`

```json
{
  "version": "0.5",
  "updated_at": "2025-11-26T12:00:00Z",
  "default_policy": {
    "max_events": 50,
    "time_window_days": null,
    "min_importance": null,
    "event_kinds": null,
    "required_tags": null,
    "excluded_tags": null
  },
  "kernel_policies": {
    "risk_model_v2": {
      "max_events": 100,
      "time_window_days": 7,
      "min_importance": 6,
      "event_kinds": ["risk_decision", "decider_outcome"],
      "required_tags": null,
      "excluded_tags": ["test"]
    },
    "trading_philosophy": {
      "max_events": 50,
      "time_window_days": 30,
      "min_importance": 7,
      "event_kinds": ["lesson", "manual_override", "trade_outcome"],
      "required_tags": ["lesson"],
      "excluded_tags": null
    },
    "system_health": {
      "max_events": 200,
      "time_window_days": 1,
      "min_importance": null,
      "event_kinds": ["system_error", "health_check", "cpu_conclusion"],
      "required_tags": null,
      "excluded_tags": null
    },
    "alpha_polymarket_core": {
      "max_events": 75,
      "time_window_days": 14,
      "min_importance": 6,
      "event_kinds": ["alpha_signal", "market_update", "trade_outcome"],
      "required_tags": null,
      "excluded_tags": ["test", "simulation"]
    }
  }
}
```

### 2. Policy Schema Definition

```python
@dataclass
class KernelHistoryPolicy:
    """
    Per-kernel history policy for filtering events

    Attributes:
        max_events: Maximum number of events to load (required)
        time_window_days: Only load events from last N days (optional, null = all time)
        min_importance: Minimum importance threshold (optional, null = no filter)
        event_kinds: List of event kinds to include (optional, null = all kinds)
        required_tags: Events must have at least one of these tags (optional, null = no requirement)
        excluded_tags: Events must NOT have any of these tags (optional, null = no exclusions)
    """
    max_events: int = 50
    time_window_days: Optional[int] = None
    min_importance: Optional[int] = None
    event_kinds: Optional[List[str]] = None
    required_tags: Optional[List[str]] = None
    excluded_tags: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "KernelHistoryPolicy":
        return cls(**data)
```

---

## Implementation Plan

### Phase 1: Config Infrastructure

**File**: `ai_nexus/history_policy.py` (new)

```python
"""
Per-kernel history policy management

Loads and applies kernel-specific history filtering policies.
"""

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List, Dict
import json
from datetime import datetime, timedelta, timezone


@dataclass
class KernelHistoryPolicy:
    """Per-kernel history policy for filtering events"""
    max_events: int = 50
    time_window_days: Optional[int] = None
    min_importance: Optional[int] = None
    event_kinds: Optional[List[str]] = None
    required_tags: Optional[List[str]] = None
    excluded_tags: Optional[List[str]] = None

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "KernelHistoryPolicy":
        # Filter out None values for cleaner serialization
        filtered_data = {k: v for k, v in data.items() if v is not None}
        return cls(**filtered_data)


def load_kernel_history_policy(kernel_id: str) -> KernelHistoryPolicy:
    """
    Load history policy for a specific kernel

    Returns kernel-specific policy if defined, otherwise returns default policy

    Args:
        kernel_id: Kernel identifier

    Returns:
        KernelHistoryPolicy object

    Example:
        policy = load_kernel_history_policy("risk_model_v2")
        # Returns policy with max_events=100, time_window_days=7, etc.
    """
    policies_file = Path(__file__).parent.parent / "ai" / "config" / "sparkplug_history_policies.json"

    # Default policy (backward compatible with v0.4)
    default_policy = KernelHistoryPolicy()

    if not policies_file.exists():
        return default_policy

    try:
        with open(policies_file) as f:
            config = json.load(f)

        # Check for kernel-specific policy
        kernel_policies = config.get("kernel_policies", {})
        if kernel_id in kernel_policies:
            return KernelHistoryPolicy.from_dict(kernel_policies[kernel_id])

        # Use default policy from config if available
        if "default_policy" in config:
            return KernelHistoryPolicy.from_dict(config["default_policy"])

        return default_policy

    except Exception as e:
        print(f"[history_policy] Warning: Failed to load policy for {kernel_id}: {e}")
        return default_policy


def apply_policy_filters(
    events: List[Dict],
    policy: KernelHistoryPolicy
) -> List[Dict]:
    """
    Apply history policy filters to a list of events

    Args:
        events: List of event dicts (from load_history_events)
        policy: KernelHistoryPolicy to apply

    Returns:
        Filtered list of events

    Example:
        events = load_history_events()
        policy = load_kernel_history_policy("risk_model_v2")
        filtered = apply_policy_filters(events, policy)
    """
    filtered = events

    # 1. Time window filter
    if policy.time_window_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=policy.time_window_days)
        filtered = [
            evt for evt in filtered
            if datetime.fromisoformat(evt["ts"].replace("Z", "+00:00")) >= cutoff
        ]

    # 2. Importance filter
    if policy.min_importance is not None:
        filtered = [
            evt for evt in filtered
            if evt.get("importance", 0) >= policy.min_importance
        ]

    # 3. Event kind filter
    if policy.event_kinds is not None:
        filtered = [
            evt for evt in filtered
            if evt.get("kind") in policy.event_kinds
        ]

    # 4. Required tags filter
    if policy.required_tags is not None:
        filtered = [
            evt for evt in filtered
            if any(tag in evt.get("tags", []) for tag in policy.required_tags)
        ]

    # 5. Excluded tags filter
    if policy.excluded_tags is not None:
        filtered = [
            evt for evt in filtered
            if not any(tag in evt.get("tags", []) for tag in policy.excluded_tags)
        ]

    # 6. Max events limit (applied last, after all filters)
    if len(filtered) > policy.max_events:
        # Keep most recent events
        filtered = sorted(filtered, key=lambda e: e["ts"], reverse=True)
        filtered = filtered[:policy.max_events]

    return filtered
```

### Phase 2: Update spark_plug_history.py

**File**: `ai_nexus/spark_plug_history.py` (update existing)

Add policy-aware loading:

```python
def load_kernel_history_events_with_policy(
    kernel_id: str,
    policy: Optional[KernelHistoryPolicy] = None
) -> List[Dict]:
    """
    Load history events for a kernel with optional policy filtering

    This is the v0.5 enhanced version that applies per-kernel policies.

    Args:
        kernel_id: Kernel to load events for
        policy: Optional policy to apply (auto-loaded if None)

    Returns:
        List of filtered event dicts

    Example:
        # Auto-load policy from config
        events = load_kernel_history_events_with_policy("risk_model_v2")

        # Or provide custom policy
        policy = KernelHistoryPolicy(max_events=10, time_window_days=1)
        events = load_kernel_history_events_with_policy("risk_model_v2", policy)
    """
    from ai_nexus.history_policy import load_kernel_history_policy, apply_policy_filters

    # Load policy if not provided
    if policy is None:
        policy = load_kernel_history_policy(kernel_id)

    # Load all events for this kernel (using existing v0.4 loader)
    # Note: We load MORE than max_events initially to allow for filtering
    raw_events = load_kernel_history_events(
        kernel_id,
        max_events=policy.max_events * 3  # Over-fetch to account for filtering
    )

    # Apply policy filters
    filtered_events = apply_policy_filters(raw_events, policy)

    return filtered_events
```

### Phase 3: Update spark_plug_autokernel.py

**File**: `ai_nexus/spark_plug_autokernel.py` (update existing)

Update `refresh_kernel_from_history()` to use policies:

```python
def refresh_kernel_from_history(
    kernel_id: str,
    max_events: Optional[int] = None,  # Now optional, uses policy if None
    cpu_profile: str = "design_only",
    conversation_id: Optional[str] = None,
    session_goal: Optional[str] = None,
    agents: Optional[List[str]] = None,
    rounds: int = 2,
    dry_run: bool = False,
    policy: Optional[KernelHistoryPolicy] = None  # New: custom policy override
) -> Dict:
    """
    Refresh a memory kernel from recent history using CPU

    v0.5 Enhancement: Now uses per-kernel history policies by default

    Args:
        kernel_id: ID of kernel to refresh
        max_events: DEPRECATED - use policy instead (kept for backward compat)
        policy: Optional custom policy (auto-loaded from config if None)
        ... (other args same as v0.4)
    """
    from ai_nexus.history_policy import load_kernel_history_policy
    from ai_nexus.spark_plug_history import load_kernel_history_events_with_policy

    # Load policy (backward compatible with max_events param)
    if policy is None:
        policy = load_kernel_history_policy(kernel_id)

        # Backward compatibility: if max_events provided, override policy
        if max_events is not None:
            policy.max_events = max_events

    # Load history events with policy filtering
    events = load_kernel_history_events_with_policy(kernel_id, policy)

    # Rest of function continues as before...
    # (build prompt, run CPU, etc.)
```

---

## Backward Compatibility

### Strategy: Graceful Degradation

1. **No config file?** → Use default policy (max_events=50, no filters)
2. **Kernel not in config?** → Use default policy
3. **Config malformed?** → Log warning, use default policy
4. **Old code calling with max_events?** → Override policy.max_events

### Migration Path

**v0.4 code (still works in v0.5):**
```python
# This continues to work exactly as before
refresh_kernel_from_history("risk_model_v2", max_events=50)
```

**v0.5 code (new):**
```python
# Uses policy from config automatically
refresh_kernel_from_history("risk_model_v2")

# Or provide custom policy
policy = KernelHistoryPolicy(max_events=10, min_importance=8)
refresh_kernel_from_history("risk_model_v2", policy=policy)
```

---

## Test Coverage Requirements

### Unit Tests

**File**: `tests/unit/test_history_policy.py` (new)

```python
"""
Unit tests for per-kernel history policy

Test coverage:
1. Policy loading (with/without config file)
2. Policy filtering (time, importance, kind, tags)
3. Backward compatibility (max_events override)
4. Error handling (malformed config)
"""

def test_load_policy_with_config():
    """Test loading kernel-specific policy from config"""
    policy = load_kernel_history_policy("risk_model_v2")
    assert policy.max_events == 100
    assert policy.time_window_days == 7
    assert policy.min_importance == 6
    assert "risk_decision" in policy.event_kinds

def test_load_policy_without_config():
    """Test default policy when no config exists"""
    # Temporarily remove config file
    policy = load_kernel_history_policy("nonexistent_kernel")
    assert policy.max_events == 50
    assert policy.time_window_days is None

def test_apply_time_window_filter():
    """Test time window filtering"""
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    events = [
        {"ts": (now - timedelta(days=1)).isoformat(), "kind": "test"},
        {"ts": (now - timedelta(days=10)).isoformat(), "kind": "test"},
    ]

    policy = KernelHistoryPolicy(time_window_days=7, max_events=100)
    filtered = apply_policy_filters(events, policy)

    assert len(filtered) == 1  # Only recent event

def test_apply_importance_filter():
    """Test importance threshold filtering"""
    events = [
        {"ts": "2025-11-26T12:00:00Z", "kind": "test", "importance": 8},
        {"ts": "2025-11-26T12:00:00Z", "kind": "test", "importance": 5},
    ]

    policy = KernelHistoryPolicy(min_importance=7, max_events=100)
    filtered = apply_policy_filters(events, policy)

    assert len(filtered) == 1
    assert filtered[0]["importance"] == 8

def test_apply_event_kind_filter():
    """Test event kind filtering"""
    events = [
        {"ts": "2025-11-26T12:00:00Z", "kind": "risk_decision"},
        {"ts": "2025-11-26T12:00:00Z", "kind": "user_message"},
    ]

    policy = KernelHistoryPolicy(
        event_kinds=["risk_decision", "decider_outcome"],
        max_events=100
    )
    filtered = apply_policy_filters(events, policy)

    assert len(filtered) == 1
    assert filtered[0]["kind"] == "risk_decision"

def test_apply_required_tags_filter():
    """Test required tags filtering"""
    events = [
        {"ts": "2025-11-26T12:00:00Z", "kind": "test", "tags": ["lesson", "important"]},
        {"ts": "2025-11-26T12:00:00Z", "kind": "test", "tags": ["routine"]},
    ]

    policy = KernelHistoryPolicy(required_tags=["lesson"], max_events=100)
    filtered = apply_policy_filters(events, policy)

    assert len(filtered) == 1
    assert "lesson" in filtered[0]["tags"]

def test_apply_excluded_tags_filter():
    """Test excluded tags filtering"""
    events = [
        {"ts": "2025-11-26T12:00:00Z", "kind": "test", "tags": ["production"]},
        {"ts": "2025-11-26T12:00:00Z", "kind": "test", "tags": ["test", "simulation"]},
    ]

    policy = KernelHistoryPolicy(excluded_tags=["test", "simulation"], max_events=100)
    filtered = apply_policy_filters(events, policy)

    assert len(filtered) == 1
    assert "production" in filtered[0]["tags"]

def test_apply_combined_filters():
    """Test multiple filters applied together"""
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    events = [
        {
            "ts": (now - timedelta(days=1)).isoformat(),
            "kind": "risk_decision",
            "importance": 8,
            "tags": ["production"]
        },
        {
            "ts": (now - timedelta(days=10)).isoformat(),
            "kind": "risk_decision",
            "importance": 9,
            "tags": ["production"]
        },
        {
            "ts": (now - timedelta(days=1)).isoformat(),
            "kind": "user_message",
            "importance": 8,
            "tags": ["production"]
        },
    ]

    policy = KernelHistoryPolicy(
        time_window_days=7,
        min_importance=7,
        event_kinds=["risk_decision"],
        excluded_tags=["test"],
        max_events=100
    )
    filtered = apply_policy_filters(events, policy)

    assert len(filtered) == 1
    assert filtered[0]["kind"] == "risk_decision"
    assert filtered[0]["importance"] == 8

def test_max_events_limit():
    """Test max_events is enforced after filtering"""
    events = [
        {"ts": f"2025-11-26T12:00:{i:02d}Z", "kind": "test"}
        for i in range(100)
    ]

    policy = KernelHistoryPolicy(max_events=10)
    filtered = apply_policy_filters(events, policy)

    assert len(filtered) == 10
    # Should keep most recent
    assert filtered[0]["ts"] > filtered[-1]["ts"]

def test_backward_compatibility_max_events_override():
    """Test that max_events parameter overrides policy"""
    # This tests the v0.4 → v0.5 backward compatibility
    policy = load_kernel_history_policy("risk_model_v2")
    assert policy.max_events == 100  # From config

    # Override in function call (v0.4 style)
    policy.max_events = 25
    assert policy.max_events == 25

def test_malformed_config_handling():
    """Test graceful degradation with malformed config"""
    # This would need to mock a malformed config file
    # Should return default policy and log warning
    pass
```

### Integration Tests

**File**: `tests/integration/test_spark_plug_with_policy.py` (new)

```python
"""
Integration tests for Spark Plug v0.5 with per-kernel policies

Tests full flow: events.jsonl → policy filter → kernel refresh
"""

def test_kernel_refresh_with_policy():
    """Test full kernel refresh flow with policy filtering"""
    # Create test events
    # Load policy
    # Run refresh_kernel_from_history
    # Verify correct events were used
    pass

def test_policy_reduces_noise_for_risk_kernel():
    """Test that risk_model_v2 policy filters out irrelevant events"""
    # risk_model_v2 should only see risk_decision and decider_outcome
    # Not user_message or other kinds
    pass

def test_policy_extends_window_for_philosophy_kernel():
    """Test that trading_philosophy gets longer time window"""
    # trading_philosophy should see 30d of events
    # risk_model_v2 should see 7d of events
    pass
```

---

## Rollout Plan

### Stage 1: Infrastructure (Low Risk)
- [ ] Create `ai_nexus/history_policy.py` with policy loading
- [ ] Create `ai/config/sparkplug_history_policies.json` with initial policies
- [ ] Write unit tests for policy loading and filtering
- [ ] **Validation**: All tests green, no changes to existing behavior

### Stage 2: Integration (Medium Risk)
- [ ] Update `spark_plug_history.py` with `load_kernel_history_events_with_policy()`
- [ ] Keep old `load_kernel_history_events()` for backward compatibility
- [ ] Write integration tests
- [ ] **Validation**: Old code still works, new code available

### Stage 3: Migration (Low Risk)
- [ ] Update `spark_plug_autokernel.py` to use policies by default
- [ ] Keep `max_events` parameter for backward compatibility
- [ ] Update documentation
- [ ] **Validation**: v0.4 code still works, v0.5 code preferred

### Stage 4: Optimization (Optional)
- [ ] Add policy caching (avoid re-reading config file)
- [ ] Add policy validation (warn about invalid configs)
- [ ] Add policy metrics (track filter effectiveness)

---

## Success Metrics

### Functional Metrics
- ✅ All existing tests pass (no regression)
- ✅ New tests achieve >90% coverage on policy code
- ✅ Backward compatibility verified (v0.4 code runs unchanged)

### Behavioral Metrics
- ✅ risk_model_v2 receives only risk-related events (not user messages)
- ✅ Time windows enforced (7d for risk, 30d for philosophy)
- ✅ Importance filtering working (low-priority events excluded)

### Performance Metrics
- ✅ Policy loading adds <1ms overhead per refresh
- ✅ Filtering reduces event volume by 40-60% (less noise for CPU)
- ✅ No increase in memory usage (filtering happens before CPU)

---

## Example Usage

### Before (v0.4):
```python
# All kernels get same treatment
refresh_kernel_from_history("risk_model_v2", max_events=50)
# Receives: risk_decision, user_message, system_error, etc. (everything)
```

### After (v0.5):
```python
# Automatic policy-based filtering
refresh_kernel_from_history("risk_model_v2")
# Receives: Only risk_decision and decider_outcome from last 7 days, importance >= 6
# 60% less noise, much more relevant context for CPU
```

### Custom Policy (v0.5):
```python
# Override policy for special refresh
policy = KernelHistoryPolicy(
    max_events=10,
    time_window_days=1,
    min_importance=9,
    event_kinds=["critical_error"]
)
refresh_kernel_from_history("system_health", policy=policy)
# Emergency refresh: only critical errors from last 24 hours
```

---

## Files to Create/Modify

### New Files
1. `ai_nexus/history_policy.py` - Policy loading and filtering logic
2. `ai/config/sparkplug_history_policies.json` - Policy configuration
3. `tests/unit/test_history_policy.py` - Policy unit tests
4. `tests/integration/test_spark_plug_with_policy.py` - Integration tests
5. `docs/SPARK_PLUG_v0.5_PER_KERNEL_HISTORY_POLICY.md` - This spec (already created)

### Modified Files
1. `ai_nexus/spark_plug_history.py` - Add `load_kernel_history_events_with_policy()`
2. `ai_nexus/spark_plug_autokernel.py` - Update `refresh_kernel_from_history()` to use policies
3. `ai_nexus/spark_plug_types.py` - Add `KernelHistoryPolicy` to exports (optional)

---

## Open Questions

### Q1: Should policies be versioned?
**Answer**: Yes - add `version` field to config for future compatibility

### Q2: Should we support policy inheritance?
**Answer**: Not in v0.5 - keep it simple. Consider for v0.6 if needed.

### Q3: Should we validate policies at load time?
**Answer**: Warn on invalid configs, but don't crash. Use defaults.

### Q4: Should we track policy effectiveness metrics?
**Answer**: Nice to have, but not required for v0.5. Consider for v0.6.

---

## Completion Criteria

This task is complete when:

1. ✅ All 5 new files created
2. ✅ All 3 modified files updated
3. ✅ All tests pass (including new policy tests)
4. ✅ Backward compatibility verified (v0.4 code runs unchanged)
5. ✅ Documentation updated
6. ✅ Example policies defined for all 5 kernels
7. ✅ Sanity check: Run `refresh_kernel_from_history("risk_model_v2")` and verify only risk events are loaded

---

## Paste-This-Into-Claude/Copilot Summary

**Task**: Implement Spark Plug v0.5 Per-Kernel History Policy

**Context**: Currently all kernels get max 50 events with no filtering. We need per-kernel policies for kind/importance/tag/time filtering.

**Files to Create**:
1. `ai_nexus/history_policy.py` - Policy loading + filtering
2. `ai/config/sparkplug_history_policies.json` - Policy config
3. `tests/unit/test_history_policy.py` - Unit tests
4. `tests/integration/test_spark_plug_with_policy.py` - Integration tests

**Files to Modify**:
1. `ai_nexus/spark_plug_history.py` - Add `load_kernel_history_events_with_policy()`
2. `ai_nexus/spark_plug_autokernel.py` - Use policies by default
3. Keep backward compatibility with `max_events` parameter

**Key Requirements**:
- Graceful degradation (no config = default policy)
- Backward compatible (v0.4 code still works)
- Test coverage >90%
- Example policies for risk_model_v2, trading_philosophy, system_health

**Success**: Run `refresh_kernel_from_history("risk_model_v2")` and verify only risk-related events from last 7 days are loaded (not user messages, etc.)

**Full Spec**: See `docs/SPARK_PLUG_v0.5_PER_KERNEL_HISTORY_POLICY.md`
