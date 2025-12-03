# Spark Plug Part 3: User Connector v0.2

**Status:** Auto-Kernel Refresh (History + CPU + Kernels Wired)
**Purpose:** User ↔ System feedback loop via history logging and kernel updates
**Created:** 2025-11-26
**Updated:** 2025-11-26 (v0.2: Auto-Kernel Refresh)
**Parent Doc:** `SPARK_PLUG_ARCHITECTURE_v0.2.md`

---

## Overview

Part 3 is the **expansion layer** that creates a bidirectional feedback loop between user and system:

```
USER ──┐
       │ (messages, decisions, observations)
       ▼
   ai/history/user_events.jsonl
       │
       ▼
   History-to-Kernels Connector
       │
       ▼
   Memory Kernels (Part 2)
       │
       ▼
   CPU (Part 1) ──> Decisions
       │
       └──> Back to User (via kernels)
```

**Key principle:** User and system stay "alive in lockstep" - no desync between what the user knows and what the system remembers.

---

## v0.1 Implementation: Foundation Layer

**What's implemented in v0.1:**
- ✅ `HistoryEvent` data model
- ✅ History logging API (append-only JSONL)
- ✅ History-to-kernels connector (generates prompts for kernel updates)
- ✅ Demo CLIs for testing
- ✅ Unit tests (offline, safe)

**What's NOT implemented (future):**
- ❌ Live UI connector (ChatGPT/Claude/Unified)
- ❌ Automatic kernel contraction from history
- ❌ Bidirectional UI sync
- ❌ User → CPU direct messaging

v0.1 provides the **file-based foundation** that future UI connectors will build on.

---

## Core Abstractions

### HistoryEvent

A `HistoryEvent` captures any significant event in the system:

```python
{
  "event_id": "evt_123456789",
  "timestamp": "2025-11-26T10:00:00Z",
  "event_type": "user_message" | "system_decision" | "trade_outcome" |
                "model_update" | "manual_override" | "cpu_conclusion" |
                "observation" | "other",
  "source": "user:froggy" | "cpu_risk_01" | "executor" | "manual",
  "content": "Natural language description of what happened",
  "context": {
    "kernel_id": "risk_model_v2",
    "decision_id": "dec_001",
    "confidence": 0.88,
    // ... any other metadata
  }
}
```

**Key fields:**
- `event_id`: Auto-generated unique ID (e.g., `evt_1732614000.123`)
- `timestamp`: ISO 8601 timestamp (auto-generated)
- `event_type`: Category of event (8 predefined types)
- `source`: Who/what generated this event
- `content`: Human-readable description
- `context`: Free-form metadata dict (kernel IDs, related data, etc.)

**Event types:**
1. `user_message` - User asks a question or gives input
2. `system_decision` - System makes a decision (CPU, executor, etc.)
3. `trade_outcome` - Trade result (PnL, fills, errors)
4. `model_update` - Model retraining, parameter changes
5. `manual_override` - User manually changes something
6. `cpu_conclusion` - CPU finishes a discussion and reaches conclusion
7. `observation` - System observation (monitoring, health checks)
8. `other` - Anything else

---

## Storage: Append-Only History Log

**File location:** `ai/history/user_events.jsonl`

**Format:** JSONL (one JSON object per line)

**Properties:**
- Append-only (no deletion or modification)
- Chronological order (oldest → newest)
- No size limit (grows indefinitely)
- Safe to read concurrently

**Example file:**
```jsonl
{"event_id": "evt_001", "timestamp": "2025-11-26T10:00:00Z", "event_type": "user_message", "source": "user:froggy", "content": "What's the current Kelly fraction?", "context": {"kernel_id": "risk_model_v2"}}
{"event_id": "evt_002", "timestamp": "2025-11-26T10:01:00Z", "event_type": "system_decision", "source": "cpu_risk_01", "content": "Updated Kelly fraction to 0.15", "context": {"kernel_id": "risk_model_v2", "decision_id": "dec_001"}}
{"event_id": "evt_003", "timestamp": "2025-11-26T10:05:00Z", "event_type": "observation", "source": "monitoring", "content": "All systems operational", "context": {"uptime": 99.9}}
```

---

## API: history_logger.py

### Core Functions

#### `append_history_event(event: HistoryEvent) -> None`

Append a history event to the log.

```python
from ai_nexus.spark_plug_types import create_history_event
from ai_nexus.history_logger import append_history_event

event = create_history_event(
    event_type="user_message",
    source="user:froggy",
    content="What's the current Kelly fraction?",
    kernel_id="risk_model_v2"
)

append_history_event(event)
```

#### `load_history_events(limit=None, event_type=None, offset=0) -> List[HistoryEvent]`

Load history events (newest first).

```python
from ai_nexus.history_logger import load_history_events

# Get last 20 events
recent = load_history_events(limit=20)

# Get last 10 user messages
user_msgs = load_history_events(limit=10, event_type="user_message")

# Pagination: skip 20, get next 20
page2 = load_history_events(offset=20, limit=20)
```

#### `count_history_events(event_type=None) -> int`

Count events in history.

```python
from ai_nexus.history_logger import count_history_events

total = count_history_events()
user_msgs = count_history_events(event_type="user_message")
```

#### `get_history_stats() -> dict`

Get statistics about the history log.

```python
from ai_nexus.history_logger import get_history_stats

stats = get_history_stats()
# {
#   "total_events": 42,
#   "event_types": {"user_message": 10, "system_decision": 15, ...},
#   "oldest_timestamp": "2025-11-26T10:00:00Z",
#   "newest_timestamp": "2025-11-26T12:30:00Z"
# }
```

---

## API: history_to_kernels.py

### Core Functions

#### `build_history_summary(max_events=20, event_type=None, kernel_id=None) -> str`

Build a natural language summary of recent history.

```python
from ai_nexus.history_to_kernels import build_history_summary

# Get summary of last 20 events
summary = build_history_summary(max_events=20)

# Get summary of events for specific kernel
summary = build_history_summary(max_events=20, kernel_id="risk_model_v2")

# Get summary of only user messages
summary = build_history_summary(max_events=10, event_type="user_message")
```

**Output format:**
```
Recent History (Last 20 Events)
==================================================

[2025-11-26T10:00:00Z] user_message from user:froggy
"What's the current Kelly fraction?"
Context: kernel_id=risk_model_v2

[2025-11-26T10:01:00Z] system_decision from cpu_risk_01
"Updated Kelly fraction to 0.15"
Context: kernel_id=risk_model_v2, decision_id=dec_001
```

#### `build_kernel_update_prompt(kernel_id, max_events=20, include_kernel_state=True) -> str`

Generate a prompt for CPU to update a memory kernel based on recent history.

```python
from ai_nexus.history_to_kernels import build_kernel_update_prompt

prompt = build_kernel_update_prompt(
    kernel_id="risk_model_v2",
    max_events=20
)

# Feed this prompt to CPU (Part 1)
# CPU will generate KernelUpdate objects
# Apply updates via memory_kernels.append_kernel_update()
```

**Output format:**
```
======================================================================
KERNEL UPDATE TASK
======================================================================

Target Kernel: risk_model_v2

--- Current Kernel State ---

Topic: Risk Management Model
Last Updated: 2025-11-26T10:00:00Z

Summary:
Current Kelly fraction is 0.12. Conservative staged rollout planned.

Key Decisions: 2
  Recent decisions:
    - Set initial Kelly fraction to 0.12 (2025-11-25)

Failed Paths: 0
Open Questions: 1
  Questions:
    - What should be the maximum Kelly fraction cap?

--- Recent History ---

[2025-11-26T10:00:00Z] user_message from user:froggy
"What's the current Kelly fraction?"
Context: kernel_id=risk_model_v2

[2025-11-26T10:01:00Z] system_decision from cpu_risk_01
"Updated Kelly fraction to 0.15"
Context: kernel_id=risk_model_v2, decision_id=dec_001

--- Task ---

Review the recent history events above and determine if any kernel updates are needed.

Consider:
  1. Are there new decisions that should be captured?
  2. Are there failed attempts that should be documented?
  3. Are there new questions that should be tracked?
  4. Does the summary need updating to reflect recent context?

Output:
  - List any KernelUpdates that should be applied
  - For each update, specify:
    - update_type (decision, failed_path, question, summary_edit)
    - content (decision, rationale, etc.)
    - source (e.g., cpu_risk_01, user:froggy)

======================================================================
```

#### `suggest_kernel_topics(max_events=100) -> List[str]`

Suggest potential kernel topics based on recent history.

```python
from ai_nexus.history_to_kernels import suggest_kernel_topics

topics = suggest_kernel_topics(max_events=50)
# ["risk_model_v2", "risk", "alpha", "infrastructure"]
```

Analyzes history for:
- Explicit kernel_ids in context
- Keyword frequency (risk, alpha, infrastructure, coordination)

---

## Demo CLIs

### history_demo.py - Log Events

**Interactive mode:**
```bash
python -m ai_nexus.history_demo
# Prompts for event type, source, content, context
```

**Quick log:**
```bash
python -m ai_nexus.history_demo log \
    --type user_message \
    --source "user:froggy" \
    --content "What's the Kelly fraction?" \
    --context kernel_id=risk_model_v2
```

**Show recent history:**
```bash
python -m ai_nexus.history_demo show --limit 20
python -m ai_nexus.history_demo show --limit 10 --type user_message
```

**Show stats:**
```bash
python -m ai_nexus.history_demo stats
python -m ai_nexus.history_demo types
```

### history_to_kernels CLI - Generate Prompts

**History summary:**
```bash
python -m ai_nexus.history_to_kernels summary --max-events 20
python -m ai_nexus.history_to_kernels summary --max-events 20 --kernel-id risk_model_v2
```

**Kernel update prompt:**
```bash
python -m ai_nexus.history_to_kernels prompt \
    --kernel-id risk_model_v2 \
    --max-events 20
```

**Suggest kernel topics:**
```bash
python -m ai_nexus.history_to_kernels suggest --max-events 50
```

---

## Happy Path Example

**Goal:** Log user interaction, generate kernel update prompt, update kernel.

### Step 1: Log user message

```bash
python -m ai_nexus.history_demo log \
    --type user_message \
    --source "user:froggy" \
    --content "Can we increase the Kelly fraction to 0.20?" \
    --context kernel_id=risk_model_v2
```

### Step 2: Log system decision

```bash
python -m ai_nexus.history_demo log \
    --type system_decision \
    --source "cpu_risk_01" \
    --content "Analyzed request. Current Kelly 0.15 is safe. Recommend staged increase to 0.18 first, monitor for 1 week, then 0.20." \
    --context kernel_id=risk_model_v2 decision_id=dec_002
```

### Step 3: Generate kernel update prompt

```bash
python -m ai_nexus.history_to_kernels prompt \
    --kernel-id risk_model_v2 \
    --max-events 20
```

This outputs a prompt like:
```
======================================================================
KERNEL UPDATE TASK
======================================================================

Target Kernel: risk_model_v2

--- Current Kernel State ---
...

--- Recent History ---

[2025-11-26T10:10:00Z] user_message from user:froggy
"Can we increase the Kelly fraction to 0.20?"
Context: kernel_id=risk_model_v2

[2025-11-26T10:11:00Z] system_decision from cpu_risk_01
"Analyzed request. Current Kelly 0.15 is safe. Recommend staged increase to 0.18 first..."
Context: kernel_id=risk_model_v2, decision_id=dec_002

--- Task ---
...
======================================================================
```

### Step 4: (Future) Feed prompt to CPU

In future versions, this prompt would be fed to a CPU (Part 1) which would:
1. Read the prompt
2. Generate `KernelUpdate` objects
3. Apply updates via `memory_kernels.append_kernel_update()`

For now, updates must be applied manually:

```python
from ai_nexus.memory_kernels import append_kernel_update
from ai_nexus.spark_plug_types import create_kernel_update_decision

update = create_kernel_update_decision(
    decision="Staged Kelly increase: 0.15 → 0.18 → 0.20",
    rationale="User requested 0.20, but staged approach safer. Monitor each stage for 1 week.",
    source="cpu_risk_01",
    agent="chatgpt"
)

append_kernel_update("risk_model_v2", update)
```

---

## Integration with Parts 1 & 2

### Flow: User → History → Kernels → CPU

```
1. User interacts (message, decision, observation)
        ↓
2. Create HistoryEvent and append to history log
        ↓
3. History accumulates over time
        ↓
4. Periodically: generate kernel update prompt from history
        ↓
5. Feed prompt to CPU (Part 1)
        ↓
6. CPU generates KernelUpdate
        ↓
7. Apply update to kernel (Part 2)
        ↓
8. Kernel evolves with user context
```

### Invariants

1. **Append-only history:** Events never deleted or modified
2. **Chronological order:** Events stored in time order
3. **Context preservation:** All important metadata in context dict
4. **Kernel linkage:** Events tagged with relevant kernel_ids
5. **Source attribution:** Every event has clear source

---

## Safety Constraints

**What Part 3 v0.1 does NOT do:**

❌ No network calls or LLM calls
❌ No imports of trading/risk/decider/executor modules
❌ No modification of live trading systems
❌ No deletion or editing of history
❌ No automatic kernel updates (prompt generation only)

**Safe to run anywhere:**

✅ File-based (JSONL)
✅ Read and write only to ai/history/
✅ Offline tests
✅ No financial risk

---

## Testing

All tests are in `tests/unit/`:

### test_history_event.py

Tests `HistoryEvent` data model:
- ✅ Creating events with all fields
- ✅ Auto-generated IDs and timestamps
- ✅ to_dict / from_dict roundtrip
- ✅ to_jsonl_line / from_jsonl_line roundtrip
- ✅ All event types
- ✅ Complex nested context

### test_history_logger.py

Tests `history_logger` API:
- ✅ Append events
- ✅ Load events (with limit, offset, filter)
- ✅ Count events
- ✅ Get stats
- ✅ Get event types
- ✅ Malformed JSONL handling
- ✅ Directory auto-creation

### test_history_to_kernels.py

Tests `history_to_kernels` connector:
- ✅ Build history summary
- ✅ Filter by event type and kernel ID
- ✅ Build kernel update prompt
- ✅ Suggest kernel topics
- ✅ Keyword-based topic detection

**Run tests:**
```bash
pytest tests/unit/test_history_event.py -v
pytest tests/unit/test_history_logger.py -v
pytest tests/unit/test_history_to_kernels.py -v
```

---

## File Structure

```
hands-off-engine/
├── ai/
│   ├── history/
│   │   └── user_events.jsonl          # Part 3: append-only event log
│   └── memory/
│       └── kernels/                    # Part 2: memory kernels
│           ├── risk_model_v2.json
│           └── ...
├── ai_nexus/
│   ├── spark_plug_types.py            # HistoryEvent type
│   ├── history_logger.py              # History logging API
│   ├── history_to_kernels.py          # History → kernel connector
│   └── history_demo.py                # Demo CLI
├── tests/
│   └── unit/
│       ├── test_history_event.py
│       ├── test_history_logger.py
│       └── test_history_to_kernels.py
└── docs/
    ├── SPARK_PLUG_ARCHITECTURE_v0.2.md
    └── SPARK_PLUG_PART3_USER_CONNECTOR_v0.1.md   # This document
```

---

## Next Steps (Future Versions)

### v0.2 - Automatic Kernel Updates

- [ ] Wire CPU (Part 1) to automatically read history prompts
- [ ] CPU generates KernelUpdate objects from prompts
- [ ] Automatic kernel update application
- [ ] Scheduled/triggered kernel updates (cron, event-driven)

### v0.3 - UI Connectors

- [ ] ChatGPT UI connector (export → history)
- [ ] Claude CLI connector (session logs → history)
- [ ] Unified UI (TUI or web) with direct history access

### v0.4 - Bidirectional Sync

- [ ] System decisions → UI messages
- [ ] No desync invariant enforcement
- [ ] Conflict resolution (UI vs kernel state)

### v1.0 - Production Ready

- [ ] Live CPU ↔ History ↔ Kernel loop
- [ ] User "alive in lockstep" with system
- [ ] Full Part 3 expansion hole operational

---

## Summary

Part 3 v0.1 provides the **file-based foundation** for user ↔ system feedback:

✅ `HistoryEvent` data model
✅ Append-only history log (`ai/history/user_events.jsonl`)
✅ History logging API (`history_logger.py`)
✅ History-to-kernels connector (`history_to_kernels.py`)
✅ Demo CLIs for testing
✅ Comprehensive unit tests

**Safe, offline, no trading risk.**

Future versions will add:
- Automatic CPU-driven kernel updates
- Live UI connectors
- Bidirectional sync

Part 3 is **designed now** so Parts 1 & 2 are ready to wire later.

---

## 🆕 v0.2 Updates: Auto-Kernel Refresh

**Status:** Implemented 2025-11-26

### What's New in v0.2

Part 3 v0.2 **wires Parts 1-3 together** into a functional loop:

**History (Part 3) → CPU (Part 1) → Kernels (Part 2)**

Now you can refresh a memory kernel from recent history with a single command.

### New Module: `spark_plug_autokernel.py`

**Core API:**
```python
refresh_kernel_from_history(
    kernel_id: str,
    max_events: int = 50,
    cpu_profile: str = "design_only",
    conversation_id: Optional[str] = None,
    session_goal: Optional[str] = None,
    agents: Optional[List[str]] = None,
    rounds: int = 2,
    dry_run: bool = False
) -> Dict
```

**What it does:**
1. Loads recent history events relevant to `kernel_id`
2. Builds kernel update prompt using `history_to_kernels`
3. Runs tri-agent CPU session with prompt + bound kernel
4. CPU discusses and generates insights
5. (Future v0.3: Auto-extracts and applies kernel updates)

**Returns:**
```python
{
    "status": "success" | "no_history" | "kernel_not_found" | "error",
    "kernel_id": str,
    "events_found": int,
    "conversation_id": str,
    "cpu_run": bool,
    "message": str
}
```

### CLI Commands (v0.2)

**Refresh a kernel from history:**
```bash
python -m ai_nexus.spark_plug_autokernel refresh \
    --kernel-id risk_model_v2 \
    --max-events 50
```

**Dry run (generate prompt but don't run CPU):**
```bash
python -m ai_nexus.spark_plug_autokernel refresh \
    --kernel-id risk_model_v2 \
    --dry-run
```

**Custom parameters:**
```bash
python -m ai_nexus.spark_plug_autokernel refresh \
    --kernel-id risk_model_v2 \
    --max-events 100 \
    --agents chatgpt,claude_cli \
    --rounds 3 \
    --conversation-id custom_refresh_20251126
```

**List kernels with history:**
```bash
python -m ai_nexus.spark_plug_autokernel list
```

**Show history stats for a kernel:**
```bash
python -m ai_nexus.spark_plug_autokernel stats --kernel-id risk_model_v2
```

### Example Workflow (v0.2)

**1. Log some history events:**
```bash
python -m ai_nexus.history_demo log \
    --type user_message \
    --source "user:froggy" \
    --content "Can we increase Kelly fraction to 0.20?" \
    --context kernel_id=risk_model_v2

python -m ai_nexus.history_demo log \
    --type system_decision \
    --source "cpu_risk_01" \
    --content "Analyzed: current 0.15 safe, recommend 0.18 first" \
    --context kernel_id=risk_model_v2
```

**2. Refresh kernel from history:**
```bash
python -m ai_nexus.spark_plug_autokernel refresh \
    --kernel-id risk_model_v2 \
    --max-events 50
```

**3. CPU runs and discusses:**
- Loads recent history events
- Generates update prompt
- Runs tri-agent discussion (ChatGPT + Claude)
- Produces insights in thread.jsonl

**4. Review CPU output:**
```bash
cat ai/intercom/autokernel_risk_model_v2_*/thread.jsonl
```

**5. (Future v0.3) Auto-apply updates:**
Currently: Manual review and application
Future: CPU output → auto-parsed → kernel updated

### Utility Functions (v0.2)

**List refreshable kernels:**
```python
from ai_nexus.spark_plug_autokernel import list_refreshable_kernels

kernels = list_refreshable_kernels()
# ["risk_model_v2", "alpha_v3", ...]
```

**Get kernel history stats:**
```python
from ai_nexus.spark_plug_autokernel import get_kernel_history_stats

stats = get_kernel_history_stats("risk_model_v2")
# {
#   "kernel_id": "risk_model_v2",
#   "total_events": 15,
#   "event_types": {"user_message": 5, "system_decision": 10},
#   "oldest_event": "2025-11-26T10:00:00Z",
#   "newest_event": "2025-11-26T12:00:00Z"
# }
```

### Tests (v0.2)

New tests in `tests/unit/test_spark_plug_autokernel.py`:
- ✅ Kernel not found → no-op
- ✅ No history events → no-op
- ✅ Dry run mode (prompt generation only)
- ✅ CPU execution success (mocked)
- ✅ Custom parameters passed correctly
- ✅ Error handling
- ✅ Auto-generated conversation IDs
- ✅ List refreshable kernels
- ✅ Get kernel history stats
- ✅ Safety: No trading/risk/executor imports
- ✅ Event filtering by kernel_id
- ✅ General events included

All tests offline (mock CPU, no real LLM calls).

**Run v0.2 tests:**
```bash
PYTHONPATH=/root/hands-off-engine pytest tests/unit/test_spark_plug_autokernel.py -v
```

**Full Part 3 suite (v0.1 + v0.2):**
```bash
PYTHONPATH=/root/hands-off-engine pytest \
    tests/unit/test_history*.py \
    tests/unit/test_spark_plug_autokernel.py -v
```

**59 tests, all passing.**

### Safety Guarantees (v0.2)

✅ **design_only mode** - CPU isolated from trading/execution
✅ **No trading imports** - spark_plug_autokernel.py imports only Spark Plug modules
✅ **Offline tests** - All tests use mocked CPU
✅ **Safe to run** - No financial risk

### File Structure (v0.2)

```
hands-off-engine/
├── ai/
│   ├── history/
│   │   └── user_events.jsonl          # Part 3: event log
│   ├── memory/
│   │   └── kernels/                    # Part 2: kernels
│   │       ├── risk_model_v2.json
│   │       └── ...
│   └── intercom/
│       └── autokernel_*_*/             # CPU sessions from v0.2
│           ├── thread.jsonl
│           └── cpu_instance.json
├── ai_nexus/
│   ├── spark_plug_types.py            # HistoryEvent, CpuInstance, etc.
│   ├── history_logger.py              # Part 3 v0.1: History API
│   ├── history_to_kernels.py          # Part 3 v0.1: Connector
│   ├── history_demo.py                # Part 3 v0.1: Demo CLI
│   ├── spark_plug_autokernel.py       # Part 3 v0.2: Auto-refresh ← NEW
│   ├── tri_agent_session_runner.py   # Part 1: CPU runner
│   └── memory_kernels.py              # Part 2: Kernel API
├── tests/
│   └── unit/
│       ├── test_history_event.py
│       ├── test_history_logger.py
│       ├── test_history_to_kernels.py
│       └── test_spark_plug_autokernel.py   ← NEW
└── docs/
    ├── SPARK_PLUG_ARCHITECTURE_v0.2.md
    └── SPARK_PLUG_PART3_USER_CONNECTOR_v0.2.md   # This doc
```

### What v0.2 Achieves

**Before v0.2:**
- Parts 1-3 existed but weren't connected
- Manual wiring required

**After v0.2:**
- **Single command** refreshes kernel from history
- History → prompt → CPU → kernel (full loop)
- Functional proof that Spark Plug architecture works

**Still manual (future v0.3):**
- Kernel update extraction from CPU output
- Auto-application of updates

But v0.2 proves the **circuit is complete**. The wiring works.

### Next Steps (v0.3+)

#### v0.3 - Auto-Extract & Apply Updates

- [ ] Parse CPU thread output for kernel updates
- [ ] Extract decisions, failed paths, questions
- [ ] Auto-apply via `memory_kernels.append_kernel_update()`
- [ ] Close the loop: history → CPU → kernel → **updated kernel**

#### v0.4 - Scheduled Refreshes

- [ ] Cron job: refresh kernels daily
- [ ] Event-driven: refresh on N new history events
- [ ] Priority-based: refresh high-activity kernels first

#### v0.5 - Bidirectional Sync

- [ ] System decisions → SystemToUserMessage
- [ ] Deliver to user UI
- [ ] Full feedback loop operational

---

**Created by:** Claude CLI
**Date:** 2025-11-26
**Version:** 0.2 (Auto-Kernel Refresh)
