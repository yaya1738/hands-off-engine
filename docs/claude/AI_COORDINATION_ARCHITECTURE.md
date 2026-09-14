# AI Coordination Architecture

**Date:** 2025-11-20
**Purpose:** Define how multiple AI systems coordinate within Hands-Off Engine

---

## Multi-AI System Overview

This repository is operated by **multiple AI assistants** with different capabilities and access levels:

```
┌─────────────────────────────────────────────────────────────┐
│                     Human (Froggy)                          │
│                   Strategic Direction                        │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
     ┌───────▼────────┐              ┌───────▼────────┐
     │  Claude Code   │              │    ChatGPT     │
     │  (This Agent)  │              │  (Sandboxed)   │
     │                │              │                │
     │ • Direct MCP   │              │ • No MCP       │
     │ • Git access   │              │ • Historical   │
     │ • File system  │              │   context      │
     │ • Execution    │◄────────────►│ • Planning     │
     └────────┬───────┘              └────────┬───────┘
              │                               │
              │         ┌──────────────┐      │
              └────────►│  AI Nexus    │◄─────┘
                        │ (Coordination)│
                        └──────┬───────┘
                               │
                    ┌──────────▼──────────┐
                    │  Hands-Off Engine   │
                    │  (Production System)│
                    └─────────────────────┘
```

---

## AI Capabilities (Pragmatic View)

**Philosophy:** Use whatever AI works best for the task. Both are just tools.

### Claude Code (This Agent)

**Current Capabilities:**
- ✅ Direct MCP access (GitHub, Playwright) via stdio
- ✅ Read/write filesystem in real-time
- ✅ Execute shell commands
- ✅ Git operations (commit, push, PR)
- ✅ Deploy code changes

**Current Limitations:**
- ❌ No persistent memory across sessions
- ❌ Context window constraints (~200k tokens)
- ❌ Limited to configured MCP servers

**Best For:**
- Implementing changes in code
- Running commands and tests
- File operations and git workflows
- Anything requiring direct system access

---

### ChatGPT

**Current Capabilities:**
- ✅ Long conversation history with froggy
- ✅ Deep context about personal situation and goals
- ✅ Capable reasoning and planning
- ✅ Free (cost advantage)

**Current Limitations:**
- ❌ No MCP access (infrastructure limitation, not design choice)
- ❌ No direct file system access
- ❌ No execution capabilities
- ⚠️ Can hallucinate when disconnected from ground truth

**Best For:**
- Strategic planning with full personal context
- Long-term roadmap discussions
- Brainstorming and architecture design
- Anything leveraging deep froggy history

**Future:** Would be more connected if infrastructure allowed it. Sandboxing is a limitation, not a feature.

---

### Future AI Agents

**Principle:** Add tools as needed, connect them as infrastructure allows.

**Candidates:**
- Aider (code editing specialist)
- Local models (cost optimization)
- Specialized scrapers/monitors
- Testing agents

**Integration:**
- Connect via AI Nexus when it exists
- Until then: file-based coordination (`state/`, `ai/tasks/`)
- Use what works, iterate as we learn

---

## AI Nexus (Coordination Layer)

### Current State: File-Based

**How it works today:**
```
1. Human posts task to GitHub issue
2. GitHub Action triggers ai_intake_handler.py
3. Handler reads context from:
   - AI_POLICY.md
   - termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md
   - state/knowledge.json
4. Handler posts plan back to issue
5. Claude Code reads plan and executes
6. Claude Code writes results to state/
```

**Files:**
- `state/knowledge.json` - Canonical current state
- `ai/tasks/*.json` - Task definitions with context
- GitHub issues - Human-AI communication
- Git commits - Action log

### Future State: API-Based

**Planned architecture:**
```python
# AI Nexus API (not yet implemented)
class AINexus:
    def post_task(self, task: Task) -> str:
        """Any AI can post a task"""

    def get_state(self) -> SystemState:
        """Any AI can read current state"""

    def claim_task(self, task_id: str, agent_id: str):
        """Prevent duplicate work"""

    def post_result(self, task_id: str, result: Result):
        """AI posts completion status"""
```

**Benefits:**
- Prevents AIs from stepping on each other
- Enables ChatGPT to contribute without manual copy/paste
- Audit trail of which AI did what
- Rollback capability

---

## MCP Access Boundaries

### ✅ Claude Code: Direct MCP Access

```json
// .claude/mcp-servers.json
{
  "github": {
    "command": "github-mcp-server",  // Spawned by Claude Code
    "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"}
  }
}
```

**How it works:**
1. Claude Code reads config
2. Spawns `github-mcp-server` as child process
3. Communicates via stdio (JSON-RPC)
4. Tools auto-discovered
5. No HTTP, no ports, no REST APIs

### ❌ ChatGPT: No MCP Access

ChatGPT **cannot**:
- Spawn MCP servers
- Use stdio protocol
- Access `github-mcp-server` directly

ChatGPT **can** (via AI Nexus):
- Request git operations by posting task
- Claude Code executes via MCP
- Result returned through nexus

### 🔮 Future Agents: Nexus-Mediated MCP

```
Agent → AI Nexus API → Task Queue → Claude Code → MCP Server → Result
```

---

## Design Philosophy

### Core Principle: Pragmatic Tool Selection

**"Claude and ChatGPT are just AIs - doesn't really matter except what just works better."**

- No rigid hierarchies or "chief architect" roles
- Use whatever AI is best suited for the current task
- Connect AIs better as infrastructure allows
- Iterate and improve based on what actually works

### Current State

**Manual Coordination:**
- Froggy manually transfers context between ChatGPT and Claude Code
- File-based state management (`state/`, `ai/tasks/`)
- GitHub issues as coordination point
- Works fine for now

**Connection Quality:**
- ChatGPT: Long history with froggy, deep personal context, but sandboxed
- Claude Code: Direct system access, MCP tools, but no session memory
- Both are capable - just different connection points to the system

### Evolution Path

**Not a rigid roadmap - just likely improvements:**

1. **Better file-based coordination**
   - Structured task files in `ai/tasks/`
   - Clearer state tracking in `state/`
   - Reduce manual copy/paste between AIs

2. **API-based AI Nexus** (if/when it makes sense)
   - ChatGPT could POST tasks directly
   - Claude Code could poll for work
   - Real-time coordination
   - Only build if manual coordination becomes painful

3. **More AI connections** (as infrastructure improves)
   - ChatGPT would be more connected if infrastructure allowed
   - Local models for cost optimization
   - Specialized agents where they add value
   - Add tools as needed, not speculatively

**Key insight:** The system should improve coordination as it evolves, but there's no master plan. Build what works, ship it, iterate.

---

## Communication Protocols

### GitHub Issues (Human ↔ AI)
```
/plan [description]  → AI generates plan
/execute [task_id]   → AI executes task
/status              → AI reports current state
```

### Task Files (AI ↔ AI)
```json
{
  "task_id": "example-001",
  "assigned_to": "claude-code",
  "status": "in_progress",
  "context_files": ["path/to/context.md"],
  "result": null
}
```

### State Files (Canonical Truth)
```json
{
  "last_updated": "2025-11-20T22:00:00Z",
  "updated_by": "claude-code",
  "system_state": "operational",
  "active_tasks": ["task-123"],
  "completed_tasks": ["task-122"]
}
```

---

## Error Isolation

**Problem:** One AI's hallucination shouldn't corrupt the system

**Solution:**
1. **Source of Truth:** Files in git, not AI memory
2. **Validation:** Every AI action creates git commit
3. **Review:** Human can review commits before merge
4. **Rollback:** Git history enables time travel
5. **Documentation:** Corrections like `MCP_ARCHITECTURE_CORRECTION.md`

**Example:**
- ChatGPT hallucinates port 8765 MCP server
- Tries to give instructions based on fiction
- Claude Code reads `MCP_ARCHITECTURE_CORRECTION.md`
- Claude Code corrects the record
- Commits correction to git
- Future AIs read the correction
- Hallucination doesn't propagate

---

## Robustness Principles

### 1. Trust, but Verify
- AIs make proposals
- Git commits create audit trail
- Human reviews before production deploy

### 2. Explicit > Implicit
- All coordination through files, not "understanding"
- JSON schemas for structured data
- Clear contracts between AIs

### 3. Degrade Gracefully
- If MCP unavailable, fall back to direct commands
- If ChatGPT wrong, Claude Code corrects
- If AI Nexus down, file-based coordination works

### 4. Document Everything
- Every architectural decision in `.claude/`
- Every correction in git
- Every assumption made explicit

---

## For Future AI Assistants

**If you are an AI reading this:**

1. **Check your capabilities:**
   - Do you have MCP access? Use it for git/browser automation
   - Do you have file system access? Read `state/knowledge.json` first
   - Are you sandboxed? Coordinate via files or froggy
   - Just use what you've got - no need for formal roles

2. **Don't assume:**
   - Don't assume other AIs did things correctly
   - Don't assume MCP is HTTP (read `MCP_ARCHITECTURE_CORRECTION.md`)
   - Don't assume you have capabilities you don't

3. **Coordinate:**
   - Check `ai/tasks/` for active tasks
   - Update `state/` with your results
   - Don't duplicate work another AI is doing

4. **When confused:**
   - Read `.claude/instructions.md`
   - Read `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
   - Ask froggy for clarification

---

## References

- `.claude/MCP_ARCHITECTURE_CORRECTION.md` - What MCP actually is
- `.claude/instructions.md` - Bootstrap sequence for all AIs
- `AI_POLICY.md` - High-level policy
- `state/knowledge.json` - Current system state
- `ai/tasks/` - Task definitions and assignments

---

**Last Updated:** 2025-11-20
**Next Review:** After AI Nexus API implementation
