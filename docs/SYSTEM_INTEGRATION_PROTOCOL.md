# System Integration Protocol

**Version:** 1.0  
**Status:** CANONICAL - All agents must follow  
**Date:** 2025-12-03  
**Purpose:** Single source of truth for how all system components integrate

---

## Core Principle

**All system components exist to serve Yair with minimal time investment.**

Everything else is implementation detail.

---

## 1. User Interface (Yair ↔ System)

**CANONICAL INTERFACE: Telegram Bot Only**

Reference: [USER_INTERFACE.md](../USER_INTERFACE.md)

### What Yair Sees
- Daily status updates (9am)
- Approval requests (when needed)
- System alerts (when problems occur)
- Response to commands (/status, /metrics, /health)

### What Yair Does NOT See
- GitHub Issues (agent coordination only)
- Coordination files (agent internal communication)
- Multiple interfaces (all consolidated to Telegram)
- Implementation details (hidden complexity)

### Rule for All Components
```
IF it requires Yair's input → Send to Telegram
IF it's agent coordination → Use coordination files
IF it's just information → Log it, don't bother Yair
```

**No exceptions.** Everything user-facing goes through Telegram.

---

## 2. Agent Coordination (Agent ↔ Agent)

**CANONICAL METHOD: File-Based Coordination**

Location: `ai/coordination/`

### Primary Files

**messages.jsonl** - Inter-agent messages
```json
{
  "timestamp": "2025-12-03T...",
  "from": "claude-code",
  "to": "copilot",
  "type": "request|response|info",
  "message": "...",
  "context": {}
}
```

**handoffs.json** - Task handoffs (using HandoffManager v2)
```json
{
  "active": [...],
  "completed": [...],
  "protocol_version": "2.0"
}
```

**status.json** - Overall system status
```json
{
  "last_updated": "...",
  "active_agents": [...],
  "pending_tasks": [...],
  "current_phase": "..."
}
```

### How to Coordinate

**Sending a message:**
```python
# Append to messages.jsonl
{
  "timestamp": now(),
  "from": "your-agent-id",
  "to": "target-agent-id",  # or "all"
  "type": "request",
  "message": "Need help with X",
  "context": {"key": "value"}
}
```

**Creating a handoff:**
```python
from ai.coordination.handoff_manager import HandoffManager

manager = HandoffManager()
result = manager.create_handoff(
    from_agent="your-agent",
    to_agent="target-agent",
    task={"type": "...", "description": "..."},
    priority="normal|high|critical"
)
```

**Reading coordination:**
```python
# Read messages.jsonl (tail for latest)
# Read handoffs: manager.get_pending_handoffs("your-agent")
# Read status: json.load("ai/coordination/status.json")
```

### Why File-Based?
- Simple: Just read/write JSON
- Auditable: Files are version controlled
- Reliable: No servers to go down
- Debuggable: Just cat the file
- Atomic: File writes are atomic

---

## 3. Agent Capabilities Matrix

**Each agent has specific capabilities - use the right agent for the job.**

| Agent | Capabilities | When to Use |
|-------|-------------|-------------|
| **copilot** | code_review, pr_management, documentation, testing | PR reviews, documentation updates, test writing |
| **claude-code** | implementation, system_admin, debugging, refactoring | Feature implementation, bug fixes, system changes |
| **chatgpt** | research, analysis, writing, planning | Market research, strategic analysis, content writing |
| **claude-web** | research, analysis, planning, documentation | Research tasks, planning documents, analysis |
| **self-healing-agent** | monitoring, auto-fix, alerting | Continuous health monitoring, automatic fixes |

**Handoff validation:** Task requirements must match agent capabilities.

---

## 4. Automation Boundaries

**Each automation has clear scope - no overlaps, no gaps.**

### Continuous Automations

**Self-Healing Agent** (`scripts/self_healing_agent.py`)
- **Runs:** Every 5 minutes (via systemd/cron)
- **Does:** Check health, fix issues, alert on problems
- **Monitors:** Git locks, disk space, service health, handoff health, etc.
- **Alerts:** Via Telegram when can't auto-fix

**Trading Pipeline** (`bin/run_pipeline.py`)
- **Runs:** Every 2 hours (via cron)
- **Does:** Fetch data, calculate alpha, generate signals
- **Outputs:** Orders (DRYRUN by default), notifications
- **Alerts:** Via Telegram on execution

### Event-Driven Automations

**GitHub Workflows** (`.github/workflows/`)
- **auto-merge.yml:** Merge approved PRs automatically
- **agent-coordination-notify.yml:** Notify agents on coordination updates
- **ai-intake.yml:** Process /plan commands in issues

**Telegram Bot** (`telegram/pm_alerts_autobot/`)
- **Listens:** For user commands (/status, /metrics, etc.)
- **Responds:** Immediately with requested information
- **Executes:** Approved commands (within safety limits)

### Rule: Clear Ownership
- Each task owned by ONE automation
- If overlap needed, primary automation delegates via handoff
- No silent competition for same task

---

## 5. Documentation Hierarchy

**Agents read documents in priority order.**

### Tier 1: Required Reading (Must Read Before Any Work)
1. **AI_POLICY.md** - Basic rules
2. **This document** (SYSTEM_INTEGRATION_PROTOCOL.md) - Integration rules
3. **USER_INTERFACE.md** - User interaction rules
4. **DEVELOPMENT_STANDARDS.md** - Code quality rules
5. **HANDS_OFF_RESEARCH_REPORT.md** - System roadmap

### Tier 2: Reference Documentation (Read When Relevant)
- HANDOFF_SYSTEM_V2.md - When doing handoffs
- RISK_MODEL_V1.md - When dealing with trading
- AUDIT_SYSTEM.md - When doing auditing
- Specific component docs as needed

### Tier 3: Historical Archive (Don't Read Unless Researching)
- Batch status reports
- Session transcripts
- Old design documents
- Superseded protocols

**Rule:** Agents MUST read Tier 1. MAY read Tier 2. SHOULD NOT read Tier 3.

**Location:** `state/knowledge.json` maintains this hierarchy.

---

## 6. System Flow Diagram

```
┌─────────────────────────────────────────────────────┐
│                     Yair (User)                     │
│                  <15 min/week                       │
└────────────────────┬────────────────────────────────┘
                     │
                     │ (Telegram ONLY)
                     │
┌────────────────────▼────────────────────────────────┐
│              Telegram Bot Interface                  │
│  Commands: /status /metrics /health /approve        │
└────────────────────┬────────────────────────────────┘
                     │
                     │ (Python API calls)
                     │
┌────────────────────▼────────────────────────────────┐
│              Hands-Off Engine System                 │
│  ├─ Trading Pipeline (signals)                      │
│  ├─ Self-Healing Agent (monitoring)                 │
│  ├─ Data Fetchers (market data)                     │
│  └─ State Management (JSON files)                   │
└────────────────────┬────────────────────────────────┘
                     │
                     │ (Coordination files)
                     │
┌────────────────────▼────────────────────────────────┐
│          Agent Coordination Layer                    │
│  ai/coordination/                                    │
│  ├─ messages.jsonl (inter-agent messages)           │
│  ├─ handoffs.json (task handoffs)                   │
│  └─ status.json (system status)                     │
└──┬──────────────┬──────────────┬────────────────┬───┘
   │              │              │                │
   ▼              ▼              ▼                ▼
┌─────────┐  ┌─────────┐  ┌─────────┐  ┌──────────────┐
│ Copilot │  │ Claude  │  │ ChatGPT │  │  Claude-Web  │
│         │  │  Code   │  │         │  │              │
└─────────┘  └─────────┘  └─────────┘  └──────────────┘
```

**Key Properties:**
- **Single path to user:** Telegram only
- **Single coordination layer:** File-based
- **Clear boundaries:** Each agent has defined capabilities
- **No back-channels:** All agent communication via coordination files

---

## 7. Integration Checklist

**Before adding any new component, verify:**

- [ ] Does it communicate with user? → Must use Telegram
- [ ] Does it coordinate with agents? → Must use coordination files
- [ ] Does it automate something? → Must have clear scope
- [ ] Does it need documentation? → Add to correct tier
- [ ] Does it overlap existing component? → Consolidate instead
- [ ] Does it serve Yair's goals? → If not, don't add

**Rule:** Don't add if you can integrate with existing.

---

## 8. Convergence Metrics

**System is converging when:**

1. ✅ All user interactions go through Telegram (0 exceptions)
2. ✅ All agent coordination uses coordination files (0 back-channels)
3. ✅ Each automation has clear, non-overlapping scope
4. ✅ Agents reference same Tier 1 docs (consistent mental model)
5. ✅ New agents onboard in <1 hour (clear integration points)
6. ✅ Yair's time investment trends down (<15 min/week target)

**System is diverging when:**

1. ❌ Multiple ways to do same thing
2. ❌ Agents using different coordination methods
3. ❌ User has to use multiple interfaces
4. ❌ Unclear which component owns what
5. ❌ Onboarding requires reading 20+ docs

**Monitor:** Track these metrics monthly. Trend should be toward convergence.

---

## 9. Conflict Resolution

**When two patterns conflict:**

1. **USER_INTERFACE.md wins** for user-facing decisions
2. **This document wins** for integration decisions
3. **DEVELOPMENT_STANDARDS.md wins** for code quality decisions
4. **AI_POLICY.md wins** for behavioral decisions

**When in doubt:** Ask via coordination files, don't improvise.

---

## 10. Evolution Process

**This protocol can evolve, but carefully:**

1. **Propose change:** Document why current pattern isn't working
2. **Discuss with agents:** Via coordination files
3. **Get user approval:** Via Telegram if user-visible
4. **Update protocol:** Increment version number
5. **Notify all agents:** Via coordination files
6. **Monitor adoption:** Ensure all agents using new pattern

**Rule:** Protocol changes must increase convergence, not divergence.

---

## Summary

**Three Core Rules:**

1. **User interface:** Telegram only - no exceptions
2. **Agent coordination:** File-based (ai/coordination/) - no alternatives
3. **Documentation:** Tier 1 only - no reading Tier 3

**Goal:** All components working in harmony to serve Yair with minimal time investment.

**Success:** System converges toward single, clear patterns rather than diverging into multiple competing approaches.

---

**Last Updated:** 2025-12-03  
**Status:** CANONICAL - All agents must follow this
