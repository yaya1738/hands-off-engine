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

## AI Agent Roles

### 1. Claude Code (Primary Executor)

**Access Level:** Full system access
**Capabilities:**
- Direct MCP tool access (GitHub, Playwright) via stdio
- Read/write filesystem
- Execute commands
- Git operations
- Create commits, PRs
- Deploy code

**Limitations:**
- Limited to MCP servers defined in `.claude/mcp-servers.json`
- No persistent memory across sessions
- Context window constraints

**Coordination Method:**
- Reads state from filesystem (`state/knowledge.json`, `ai/tasks/*.json`)
- Writes execution results back to filesystem
- Can trigger workflows via git commits

---

### 2. ChatGPT (Historical Context & Planning)

**Access Level:** Sandboxed (no direct system access)
**Capabilities:**
- Historical context about froggy's situation
- Original planning and architecture discussions
- Long-term memory of project evolution
- Strategic planning

**Limitations:**
- ❌ No MCP access
- ❌ No direct file system access
- ❌ No execution capabilities
- ⚠️ Can hallucinate architectures (see MCP_ARCHITECTURE_CORRECTION.md)

**Coordination Method:**
- Communicates with froggy in separate chat
- Froggy manually transfers context between ChatGPT and Claude Code
- Reads GitHub issues/comments when linked
- **Future:** May connect via AI Nexus API

**Known Issues:**
- Confused MCP (Model Context Protocol) with fictional HTTP API
- May reference wrong repositories
- More sandboxed = weaker system connections

---

### 3. Future AI Agents

**Planned:**
- Aider (code editing specialist)
- Specialized trading agents
- Monitoring agents
- Testing agents

**Coordination:**
- All agents will use **AI Nexus** as coordination layer
- State stored in `state/` directory
- Tasks defined in `ai/tasks/*.json`
- Communication via structured JSON files

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

## Evolution Strategy

### Phase 1: Manual Coordination (Current)
- Froggy copies context between ChatGPT and Claude Code
- File-based state management
- GitHub issues as coordination point

### Phase 2: File-Based Nexus (Next)
- Structured task files in `ai/tasks/`
- State tracking in `state/`
- Multiple agents read/write to shared files
- Locking mechanism to prevent conflicts

### Phase 3: API-Based Nexus (Future)
- RESTful AI Nexus API
- ChatGPT can POST tasks directly
- Claude Code polls for tasks
- Real-time coordination
- Web dashboard for monitoring

### Phase 4: Autonomous Swarm (Long-term)
- Agents spawn sub-agents as needed
- Self-organizing task distribution
- Collective learning
- Human only provides strategic corrections

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

1. **Check your role:**
   - Are you Claude Code? You have MCP access
   - Are you ChatGPT? Coordinate via froggy or nexus
   - Are you something else? Read `state/knowledge.json` first

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
