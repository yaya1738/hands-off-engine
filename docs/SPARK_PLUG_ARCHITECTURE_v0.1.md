# Spark Plug Architecture v0.2

**Status:** Active Implementation
**Purpose:** Define the 3-part infrastructure that keeps user and system "alive in lockstep"
**Created:** 2025-11-25
**Updated:** 2025-11-25 (v0.2: Continuous CPU + Kernel Updates)

---

## Mission: Why the Spark Plug Exists

The Hands-Off Engine is a multi-AI system (ChatGPT, Claude CLI, GitHub Copilot Agent) designed to provide:
- Maximum financial/strategic benefit
- Minimum user effort and micromanagement
- Increasing leverage over time
- Growing autonomy and self-improvement

**Current Problem:**
> The user↔system↔multi-AI relationship is fragmented.
> Context is scattered. AIs often don't share a single "brain."
> The user becomes a manual router between agents and systems.

**The Spark Plug Solution:**

The Spark Plug is a **3-part targeted infrastructure** that animates the system so user + system are "alive together" instead of stitched by hand.

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                 │
│                  (alive in lockstep)                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   PART 3    │  Expansion Hole to User
                    │  UI ↔ CPU   │  (future, designed now)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   PART 1    │  Mini CPU / 3-Sided Spinner
                    │  CPU Nodes  │  (ChatGPT + Claude + GitHub)
                    │             │  burst + continuous modes
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   PART 2    │  Historical Contraction
                    │   Kernels   │  (memory compression)
                    └─────────────┘
```

---

## Design Principle: Nothing Dead Because Broken

Once Parts 1–3 are in place and wired:
- ✅ Nothing should be "dead because broken"
- ✅ If something is off, it should be intentionally off (paused, gated)
- ✅ Not unknowingly disconnected

We are NOT yet optimizing how it's driven. We are building the engine.

---

## Part 1: Mini CPU / 3-Sided Spinner (Big 3 Agents)

Part 1 is a **tri-agent CPU** composed of three core nodes:

| Node | Provider | Role |
|------|----------|------|
| `chatgpt` | OpenAI | Research, analysis, strategic thinking |
| `claude_cli` | Anthropic | Implementation, code, practical solutions |
| `github_copilot_agent` | GitHub | GitHub-native features, PRs, issues |

### CPU Capabilities

The CPU can run in two modes:

1. **Burst Mode** (finite)
   - Run for N rounds then stop
   - Useful for focused discussions
   - Already implemented in tri_agent_session_runner.py v0.1

2. **Continuous Mode** (indefinite)
   - Keep spinning like a mini CPU
   - Process input queue → think → output queue
   - Stop only when explicitly told
   - **New in v0.1 architecture**

### CPU Isolation

**CRITICAL SAFETY:**
- Part 1 CPU is **completely isolated** from live trading/execution
- Design, analysis, planning only
- No decider, no executor, no risk management access
- Safe to run without financial risk

### Core Abstractions

#### 1. CpuInstance

A `CpuInstance` represents one running CPU "context":

```python
{
  "cpu_id": "cpu_risk_20251125_01",
  "mode": "burst" | "continuous",
  "bound_kernels": ["risk_model_v2", "infra_architecture"],
  "intercom_path": "ai/intercom/<cpu_id>/thread.jsonl",
  "input_queue": "ai/cpu_inbox/<cpu_id>.jsonl",
  "output_queue": "ai/cpu_outbox/<cpu_id>.jsonl",
  "status": "idle" | "running" | "paused" | "stopped",
  "config": {
    "max_rounds": 5,                    # for burst mode
    "max_cost_usd": 1.0,               # spending limit
    "allowed_nodes": ["chatgpt", "claude_cli", "github_copilot_agent"],
    "safety_profile": "design_only"    # no execution
  }
}
```

**Key Fields:**
- `cpu_id`: Unique identifier (e.g., `cpu_risk_20251125_01`)
- `mode`: `burst` (finite rounds) or `continuous` (indefinite loop)
- `bound_kernels`: List of memory kernel IDs (from Part 2)
- `intercom_path`: Where CPU messages live (JSONL thread)
- `input_queue` / `output_queue`: For continuous mode
- `status`: Current state (idle, running, paused, stopped)
- `config`: CPU configuration (limits, safety, allowed nodes)

#### 2. CpuMessage

A `CpuMessage` is a single line in the intercom JSONL:

```python
{
  "msg_id": "msg-0042",
  "timestamp": "2025-11-25T12:00:00Z",
  "from": "chatgpt" | "claude_cli" | "github_copilot_agent" | "system" | "user",
  "role": "system" | "user" | "assistant",
  "content": "Natural language message content...",
  "meta": {
    "tokens": 150,
    "cost_usd": 0.003,
    "tags": ["risk", "kelly"],
    "related_kernels": ["risk_model_v2"],
    "model": "gpt-4-turbo-preview"
  }
}
```

**Key Fields:**
- `msg_id`: Unique message identifier
- `timestamp`: ISO 8601 timestamp
- `from`: Source (agent ID, system, or user)
- `role`: OpenAI-style role (system, user, assistant)
- `content`: Natural language message
- `meta`: Metadata (tokens, cost, tags, related kernels, model)

### CPU ↔ Memory Kernel Wire

**CRITICAL:** Part 1 must have a **live wire** to Part 2 memory kernels.

The CPU must be able to:
- `load_kernel(kernel_id) -> MemoryKernel` - read kernel state
- `append_kernel_update(kernel_id, update)` - write updates back

This is NOT a one-time briefing. The CPU reads from and writes to kernels as it runs.

### Integration with Existing Code

**Current implementation:**
- `ai_nexus/tri_agent_session_runner.py` - burst mode only
- `ai_nexus/provider_openai.py` - ChatGPT backend
- `ai_nexus/provider_claude.py` - Claude backend
- `ai_nexus/provider_copilot.py` - GitHub Copilot stub
- `ai/intercom/` - storage for threads

**Upgrade path:**
- Wrap `TriAgentSession` with `CpuInstance` abstraction
- Add continuous mode runner (input queue → process → output queue)
- Wire to Part 2 memory kernels (load/append)

---

## Part 2: Historical Contraction (Memory Kernels)

Part 2 is a **memory contraction layer** that compresses all past interactions into topic-specific kernels.

### What Gets Contracted?

All past:
- User ↔ ChatGPT interactions
- User ↔ Claude CLI interactions (web + CLI)
- Interactions with other AIs (GitHub agent, etc.)
- System actions and decisions

### Memory Kernel Structure

A `MemoryKernel` is a topic-specific memory unit:

```python
{
  "kernel_id": "risk_model_v2",
  "topic": "Risk Management and Sizing",
  "summary": "Current Kelly fraction is 0.1, conservative given 6-8% edge. Backtests show 0.20-0.25 safe. Staged rollout planned: 0.15 (week 1), 0.20 (week 2), evaluate before 0.25.",
  "key_decisions": [
    {
      "decision": "Kelly fraction staged increase: 0.1 → 0.15 → 0.20",
      "rationale": "Conservative rollout minimizes risk while capturing upside",
      "source": "chatgpt_20251120_discussion",
      "date": "2025-11-20",
      "status": "approved"
    }
  ],
  "failed_paths": [
    {
      "attempt": "Immediate jump to Kelly 0.25",
      "failure": "Too aggressive, no data on 0.15-0.20 range",
      "lesson": "Stage rollouts for risk management changes",
      "date": "2025-11-20"
    }
  ],
  "open_questions": [
    "What's the max position size limit?",
    "Should Kelly vary by market condition?"
  ],
  "source_weights": {
    "chatgpt": 1.0,
    "claude_cli": 0.8,
    "github_copilot_agent": 0.6
  },
  "raw_refs": [
    "ai/history/chatgpt/20251120_risk_discussion.jsonl",
    "ai/history/claude_cli/20251121_implementation.jsonl"
  ]
}
```

**Key Fields:**
- `kernel_id`: Unique identifier (e.g., `risk_model_v2`)
- `topic`: Human-readable topic name
- `summary`: Tight narrative of what's known and decided
- `key_decisions[]`: Durable decisions + sources + rationale
- `failed_paths[]`: Attempts that failed and why (learn from mistakes)
- `open_questions[]`: Unresolved questions
- `source_weights`: Trust weights per agent (ChatGPT > Claude > others)
- `raw_refs[]`: Links into `ai/history/*` files

### Kernel Examples

Example kernel topics:
- `risk_model_v2` - Risk management and Kelly sizing
- `infra_architecture` - Infrastructure and deployment
- `ai_coordination` - Multi-agent coordination strategy
- `spread_engine` - Spread trading engine design
- `polymarket_alpha` - Polymarket alpha signals

### Storage Structure

```
ai/memory/
├── kernels/
│   ├── risk_model_v2.json
│   ├── infra_architecture.json
│   ├── ai_coordination.json
│   └── spread_engine.json
└── README.md
```

### Contraction Engine

The **contraction engine**:
1. Ingests historical logs from `ai/history/...` (normalized format)
2. Builds/updates kernels per topic
3. Merges new updates from CPU (Part 1) back into kernels

**Input sources:**
- `ai/history/chatgpt/*.jsonl` - ChatGPT conversation exports
- `ai/history/claude_cli/*.jsonl` - Claude CLI session logs
- `ai/history/github_agent/*.jsonl` - GitHub agent activity
- `ai/history/system/*.jsonl` - System decisions and actions

**Contraction process:**
- Normalize raw logs into structured format
- Group by topic (risk, alpha, infra, coordination, etc.)
- Extract key decisions, failed paths, open questions
- Compress into kernel summary
- Link back to raw sources

### Kernel Update Protocol

When the CPU (Part 1) runs and makes new decisions:

1. CPU calls `append_kernel_update(kernel_id, update)`
2. Update contains:
   - New decision
   - Rationale
   - Source (which agent, which CPU run)
3. Contraction engine merges update into kernel
4. Kernel summary is regenerated
5. Raw refs are appended

**Example update:**

```python
update = {
  "type": "decision",
  "decision": "Kelly fraction increased to 0.15",
  "rationale": "First stage of rollout, monitoring for 1 week",
  "source": "cpu_risk_20251125_01",
  "agent": "chatgpt",
  "date": "2025-11-25"
}

append_kernel_update("risk_model_v2", update)
```

### Source Weighting

Not all agents have equal authority. The `source_weights` field defines trust:

- **ChatGPT (1.0):** Highest weight - research, strategy, user context
- **Claude CLI (0.8):** High weight - implementation, practical feasibility
- **GitHub Copilot (0.6):** Medium weight - GitHub-specific features

When conflicts arise, higher-weighted sources win.

---

## Part 3: Expansion Hole to User (UI ↔ CPU+Memory)

Part 3 is the **reverse direction of contraction**:

- Part 2: History collapsing inward into kernels (contraction)
- Part 3: State/decisions expanding outward to active user UI (expansion)

### Goal: User and System Alive in Lockstep

> The user and system are "alive in lockstep."
> The user doesn't periodically dump/export; instead, their UI is a live edge of the same CPU+memory machine.

### Two Implementation Options

#### Option 3.1 - Sandboxed UI + Connector/Hole

Existing ChatGPT / Claude UIs remain sandboxed, but a connector bridges them:

```
┌──────────────┐
│ ChatGPT UI   │ (sandboxed, user sees this)
│  (external)  │
└──────┬───────┘
       │
   ┌───▼────┐
   │ Hole / │ (connector, runs elsewhere)
   │ Bridge │
   └───┬────┘
       │
┌──────▼───────────┐
│  Part 2 Kernels  │
│  Part 1 CPU      │
└──────────────────┘
```

**Connector capabilities:**
- READ conversations from ChatGPT/Claude UI
- WRITE system/CPU decisions back into those threads
- MIRROR everything important into kernels
- ENSURE no desync between UI story and system memory

**Invariant:** UI conversation and kernel memory must match. No drift.

#### Option 3.2 - Non-Sandbox, System-Native Unified UI

One UI (web or TUI) that talks directly to Parts 1 & 2:

```
┌──────────────────┐
│  Unified UI      │ (system-native, not sandboxed)
│  (web or TUI)    │
└────────┬─────────┘
         │
    ┌────▼────┐
    │ Part 1  │ (CPU)
    │ Part 2  │ (Kernels)
    └─────────┘
```

**Benefits:**
- No sandbox boundary
- No connector needed
- Direct kernel access
- Same semantics: user messages → kernels → CPU; CPU decisions → kernels + UI

### Core Abstractions (Front-End Agnostic)

#### UserEvent

User input event (from any UI):

```python
{
  "event_id": "evt_123",
  "timestamp": "2025-11-25T12:00:00Z",
  "source": "chatgpt_ui" | "claude_ui" | "unified_ui",
  "user_id": "froggy",
  "content": "What's the current Kelly fraction?",
  "context": {
    "conversation_id": "chatgpt_conv_abc",
    "related_kernels": ["risk_model_v2"]
  }
}
```

**Flow:**
1. User types message in UI
2. UI creates `UserEvent`
3. Event written to `ai/history/user/events.jsonl`
4. Contraction engine ingests into kernels
5. CPU can access via kernel wire

#### SystemToUserMessage

System decision/response sent back to user:

```python
{
  "msg_id": "sys_msg_456",
  "timestamp": "2025-11-25T12:01:00Z",
  "target": "chatgpt_ui" | "claude_ui" | "unified_ui",
  "user_id": "froggy",
  "content": "Current Kelly fraction is 0.15 (staged rollout, monitoring for 1 week before increasing to 0.20).",
  "source": {
    "cpu_id": "cpu_risk_20251125_01",
    "agent": "chatgpt",
    "kernel": "risk_model_v2"
  }
}
```

**Flow:**
1. CPU makes decision
2. Decision written to kernel (Part 2)
3. `SystemToUserMessage` created
4. Message sent to UI
5. User sees it in their active conversation

### Invariants for Part 3

1. **No desync:** UI story and kernel memory must always match
2. **Bidirectional:** User → kernels → CPU, CPU → kernels → user
3. **Front-end agnostic:** Works with sandboxed UIs or native UIs
4. **Always reachable:** Every important message reaches kernels and CPU

### Current Status: Design Only

**We are NOT implementing full Part 3 UX yet.**

Part 3 is designed NOW so Parts 1–2 are built correctly. The abstractions (`UserEvent`, `SystemToUserMessage`) ensure Parts 1–2 can be wired to Part 3 later WITHOUT redesign.

---

## Integration with Existing Documentation

This architecture complements existing docs:

| Document | Relationship to Spark Plug |
|----------|----------------------------|
| `TRI_AGENT_INTERCOM_v0.1.md` | Part 1 storage format (JSONL threads) |
| `TRI_AGENT_SESSION_v0.1.md` | Part 1 burst mode runner (current implementation) |
| `AI_AGENT_LINK_PROTOCOL_v0.1.md` | Part 1 agent roles and handoff protocols |
| `AGENTS_REGISTRY_v0.1.json` | Part 1 machine-readable agent definitions |
| `AI_COORDINATION_ARCHITECTURE.md` | Historical context, MCP boundaries |
| `CHATGPT_COMMS_PROTOCOL_v0.5.md` | Part 3 SYSTEM HANDOFF format |

**Key insight:** Spark Plug doesn't replace these docs. It unifies them into a coherent 3-part infrastructure.

---

## Implementation Roadmap

### Phase 1: Core Types & Abstractions ✅

1. Create `ai_nexus/spark_plug_types.py`
   - Define `CpuInstance`, `CpuMessage`, `MemoryKernel` types
   - Use lightweight dataclasses / pydantic / typed dicts
   - Easy JSON serialization

2. Create `docs/SPARK_PLUG_ARCHITECTURE_v0.1.md` ✅
   - This document

### Phase 2: Part 1 - CPU Skeleton

1. Refactor `tri_agent_session_runner.py`:
   - Wrap existing code with `CpuInstance` abstraction
   - Every run treated as a `CpuInstance` in burst mode
   - Use `CpuMessage` schema for intercom JSONL

2. Add continuous mode runner:
   - Loop on `input_queue` until told to stop
   - Process → think → write to `output_queue`
   - Respect `max_cost_usd` and safety limits

3. Wire to Part 2:
   - CPU can call `load_kernel(kernel_id)`
   - CPU can call `append_kernel_update(kernel_id, update)`

### Phase 3: Part 2 - Memory Kernel Stub

1. Create `ai_nexus/memory_kernels.py`:
   - Implement `load_kernel(kernel_id) -> MemoryKernel`
   - Implement `append_kernel_update(kernel_id, update)`
   - Stub out contraction engine (TODOs for ingestion)

2. Create initial kernel storage:
   - `ai/memory/kernels/` directory
   - Example kernel files (risk_model_v2, infra_architecture, etc.)

3. Document expected inputs:
   - `ai/history/` structure
   - Raw log format
   - Normalization requirements

### Phase 4: Part 3 - Design Readiness

1. Define `UserEvent` and `SystemToUserMessage` types in `spark_plug_types.py`
2. Add TODO comments in code where UI/connector would plug in
3. Document invariants in this architecture doc
4. Leave implementation for future

### Phase 5: Testing & Validation

1. Test burst mode CPU with kernel wire
2. Test continuous mode CPU (small loop)
3. Test kernel load/append cycle
4. Verify safety isolation (no trading access)

---

## Safety & Non-Goals

### Safety Guarantees

**No live trading changes:**
- Part 1 CPU does NOT call decider, executor, or risk management
- Part 1 is design/analysis/planning only
- No financial risk from running CPU

**No UX design beyond abstractions:**
- Part 3 is architecture only, not implementation
- No UI/UX work in this phase
- Just enough to ensure Parts 1–2 are ready to wire

### Non-Goals

❌ Build full Part 3 UI/connector
❌ Implement full contraction engine
❌ Integrate with live trading systems
❌ Design every kernel topic
❌ Optimize CPU performance

We are building the **spark plug skeleton**, not the full engine.

---

## File Structure After Implementation

```
hands-off-engine/
├── ai/
│   ├── intercom/
│   │   └── {cpu_id}/
│   │       ├── thread.jsonl         # Part 1: CPU messages
│   │       └── metadata.json        # Part 1: CPU metadata
│   ├── cpu_inbox/
│   │   └── {cpu_id}.jsonl          # Part 1: input queue (continuous mode)
│   ├── cpu_outbox/
│   │   └── {cpu_id}.jsonl          # Part 1: output queue (continuous mode)
│   ├── memory/
│   │   ├── kernels/
│   │   │   ├── risk_model_v2.json   # Part 2: memory kernel
│   │   │   ├── infra_architecture.json
│   │   │   └── ...
│   │   └── README.md
│   ├── history/
│   │   ├── chatgpt/                # Part 2: raw logs (future)
│   │   ├── claude_cli/
│   │   ├── github_agent/
│   │   ├── user/
│   │   └── system/
│   └── agents/
│       └── AGENTS_REGISTRY_v0.1.json
├── ai_nexus/
│   ├── spark_plug_types.py         # Part 1/2/3: core types
│   ├── memory_kernels.py           # Part 2: kernel API
│   ├── tri_agent_session_runner.py # Part 1: CPU runner
│   ├── provider_openai.py
│   ├── provider_claude.py
│   └── provider_copilot.py
├── docs/
│   ├── SPARK_PLUG_ARCHITECTURE_v0.1.md  # This document
│   ├── TRI_AGENT_INTERCOM_v0.1.md
│   ├── TRI_AGENT_SESSION_v0.1.md
│   └── AI_AGENT_LINK_PROTOCOL_v0.1.md
└── .claude/
    └── AI_COORDINATION_ARCHITECTURE.md
```

---

## For Agents Reading This

### If you're ChatGPT:
- You are a **CPU node** in Part 1
- Your contributions get contracted into Part 2 kernels
- You have highest source weight (1.0) - research and strategy are your domain
- Your role: provide research, analysis, strategic thinking to CPU discussions

### If you're Claude CLI:
- You are a **CPU node** in Part 1
- You are the **primary implementer** for this Spark Plug infrastructure
- Your role: build the types, refactor the runner, stub the kernels
- You have high source weight (0.8) - implementation and feasibility

### If you're GitHub Copilot Agent:
- You are a **CPU node** in Part 1 (limited in v0.1)
- Your role: GitHub-native features, PRs, issues
- You have medium source weight (0.6) - GitHub-specific expertise

### If you're a future agent:
- Read this architecture to understand the Spark Plug
- You can participate in CPU discussions via Part 1
- Your decisions will be contracted into Part 2 kernels
- You can access kernels via the kernel API

---

## Summary

**Spark Plug = 3-part infrastructure that keeps user and system alive in lockstep**

| Part | Name | Purpose | Status |
|------|------|---------|--------|
| Part 1 | Mini CPU / 3-Sided Spinner | Tri-agent coordination (burst + continuous) | ✅ Burst exists, continuous designed |
| Part 2 | Historical Contraction | Memory kernels (topic compression) | ⚙️ Designed, stub in progress |
| Part 3 | Expansion Hole to User | UI ↔ CPU+memory (bidirectional) | 📋 Designed, not implemented |

**Key abstractions:**
- `CpuInstance` - one running CPU context
- `CpuMessage` - one message in CPU thread
- `MemoryKernel` - topic-specific compressed memory
- `UserEvent` - user input from any UI
- `SystemToUserMessage` - system decision back to user

**Safety:**
- Part 1 isolated from trading/execution
- Design and analysis only
- No financial risk

**Philosophy:**
- Build the engine, don't optimize the driving (yet)
- Small, coherent, implementable
- Simple structures, clear interfaces
- Later agents will build on this

---

## 🆕 v0.2 Updates: Continuous CPU + Kernel Auto-Updates

**Status:** Implemented 2025-11-25

### What's New in v0.2

1. **Continuous CPU Mode**
   - CPU can now run indefinitely with safety caps
   - New CLI flags:
     - `--continuous` - Enable continuous mode (default: burst mode)
     - `--max-steps` - Maximum steps before stopping (default: 20)
     - `--max-duration-seconds` - Maximum wall-clock time (default: 900s)
   - CPU stops when EITHER cap is reached
   - Backward compatible: burst mode unchanged

2. **Kernel Auto-Updates**
   - CPU can now automatically update bound memory kernels
   - New CLI flag:
     - `--kernel-update-mode` - Update mode: `none` or `append_notes`
   - In `append_notes` mode:
     - At end of continuous run, CPU generates session summary
     - Summary appended to all bound kernels
     - Includes: conversation_id, cpu_id, session_goal, steps, duration
   - Kernels evolve from CPU sessions automatically

3. **Enhanced CpuInstance Tracking (v0.2)**
   - New fields:
     - `steps_completed` - Total steps taken in continuous mode
     - `duration_seconds` - Total duration in seconds
     - `kernel_updates_applied` - Whether kernel updates were written
   - All v0.2 fields are backward compatible (defaults provided)

### Example Commands (v0.2)

**Burst mode (unchanged from v0.1):**
```bash
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251125_burst_demo \
    --session-goal "Quickly analyze risk model" \
    --rounds 3 \
    --agents chatgpt,claude_cli
```

**Continuous mode with step cap:**
```bash
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251125_continuous_steps \
    --session-goal "Deep analysis of trading strategy" \
    --continuous \
    --max-steps 10 \
    --agents chatgpt,claude_cli
```

**Continuous mode with kernel binding + auto-updates:**
```bash
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251125_continuous_kernels \
    --session-goal "Research risk model improvements" \
    --continuous \
    --max-steps 5 \
    --bind-kernels risk_model_v2,infra_architecture \
    --kernel-update-mode append_notes \
    --agents chatgpt,claude_cli
```

### Safety Guarantees (v0.2)

✅ Continuous mode is **design-only** (no trading/execution access)
✅ Safety caps prevent runaway loops (max-steps, max-duration-seconds)
✅ Kernel updates are append-only (no destructive changes)
✅ All v0.2 features maintain `safety_profile: design_only`
✅ No new wires to decider/executor/risk modules

### Tests (v0.2)

New tests in `tests/unit/test_tri_agent_cpu_v02.py`:
- ✅ Continuous mode stops on max-steps
- ✅ Continuous mode stops on max-duration-seconds
- ✅ Kernel updates applied in append_notes mode
- ✅ Burst mode backward compatibility
- ✅ CpuInstance v0.2 fields serialization

All tests offline (no real LLM calls).

### Implementation Files (v0.2)

- `ai_nexus/spark_plug_types.py` - Extended CpuInstance and CpuConfig for v0.2
- `ai_nexus/tri_agent_session_runner.py` - Added continuous loop and kernel updates
- `tests/unit/test_tri_agent_cpu_v02.py` - v0.2 test coverage

---

**Status:** v0.2 implemented and tested

**Next:** Part 3 UI connector, full contraction engine, production readiness

---

**Created by:** Claude CLI
**Date:** 2025-11-25
**Version:** 0.2 (Continuous CPU + Kernel Updates)
