# AI Agent Link Protocol v0.1

**Status:** Active
**Purpose:** Define how multiple AI agents coordinate in the Hands-Off Engine system
**Scope:** Documentation layer - no runtime behavior changes

---

## Purpose

This protocol establishes a **lightweight linking layer** between the three primary AI agents working in the Hands-Off Engine:

1. **ChatGPT** - Research and design
2. **Claude CLI** - Primary implementation
3. **GitHub Copilot Agent** - GitHub-native assistance

**Why this matters:**
- Multiple AIs work better than one
- Each AI has strengths - use them appropriately
- Need shared understanding of roles and handoffs
- Prevent confusion about who does what

**Key principle:** Use whatever AI works best for each task. No rigid hierarchies, just clear handoff protocols.

---

## Agents

### 1. ChatGPT (`chatgpt`)

**Role:** Research, strategy, architecture, design

**Strengths:**
- Deep research and analysis
- Architectural planning
- Brainstorming and ideation
- Design decisions
- Strategic thinking

**Input:** User conversations

**Output:** SYSTEM HANDOFF blocks (see `docs/CHATGPT_COMMS_PROTOCOL_v0.5.md`)

**Repo access:** None - does not touch repo directly

**Typical workflow:**
1. User discusses problem/idea with ChatGPT
2. ChatGPT researches, designs, plans
3. ChatGPT creates SYSTEM HANDOFF block
4. User copies and pastes to Claude CLI or GitHub Copilot Agent

---

### 2. Claude CLI (`claude_cli`)

**Role:** Primary code and documentation implementer in repo

**Strengths:**
- Code implementation
- File editing and creation
- Git operations
- Complex multi-file changes
- Documentation writing
- System integration

**Input:**
- SYSTEM HANDOFF blocks (from ChatGPT via user)
- `ai/tasks/*.json` task files
- `.claude/instructions.md` directives
- Direct user requests in CLI

**Output:**
- Git commits
- Documentation in `docs/`
- Task updates in `ai/tasks/`
- Code changes across repo

**Repo access:** Full - primary implementer

**Typical workflow:**
1. Receives SYSTEM HANDOFF or task
2. Validates target and context
3. Implements changes across multiple files
4. Commits with descriptive messages
5. Pushes to GitHub

---

### 3. GitHub Copilot Agent (`github_copilot_agent`)

**Human label:** "GitHub Copilot Agent"

**Role:** GitHub-native helper for issues, PRs, and AI-intake workflow

**Strengths:**
- GitHub issue management
- Pull request creation and review
- AI-intake workflow responses
- Status updates and comments
- GitHub-native integrations

**Input:**
- GitHub issue comments
- Pull request comments
- AI-intake workflow triggers (e.g., `/plan` command)
- Optionally: SYSTEM HANDOFF text if user pastes into issues

**Output:**
- Pull requests
- Commits (via PRs)
- Issue comments
- Status updates

**Repo access:** Via GitHub APIs and workflows

**Typical workflow:**
1. Monitors GitHub issues/PRs
2. Responds to AI-intake commands
3. Creates PRs for changes
4. Provides status updates
5. Collaborates with Claude CLI via repo

---

## Communication Flows (v0.1)

### Primary Flow: ChatGPT → Claude CLI → Repo

```
User ← → ChatGPT (research/design)
         ↓
    SYSTEM HANDOFF block
         ↓
User copy-pastes
         ↓
    Claude CLI (implementation)
         ↓
    Git commits → GitHub repo
```

**Most common path for:**
- New features from research
- Architectural changes
- Complex implementations
- Documentation from design discussions

---

### Secondary Flow: ChatGPT → GitHub Copilot Agent → Repo

```
User ← → ChatGPT (research/design)
         ↓
    SYSTEM HANDOFF block
         ↓
User pastes into GitHub Issue
         ↓
GitHub Copilot Agent (implementation)
         ↓
    Pull Request → GitHub repo
```

**Used for:**
- Changes better suited to PR workflow
- When GitHub-native features needed
- Collaborative review desired upfront

---

### Collaboration Flow: Claude CLI ↔ GitHub Copilot Agent

```
    Claude CLI
         ↓
    Commits to repo
         ↓
   GitHub repo (shared source of truth)
         ↓
GitHub Copilot Agent sees changes
         ↓
Can create PRs, issues, comments
```

**Bidirectional via repo:**
- Claude CLI commits
- GitHub Copilot Agent sees commits
- Can comment, create issues, suggest changes
- Both agents share repo as coordination point

---

## Handoff Protocols

### ChatGPT → Claude CLI / GitHub Copilot Agent

**Protocol:** SYSTEM HANDOFF v0.5

**Format:**
```
=== SYSTEM HANDOFF: [TITLE] ===
TARGET: [Agent]
INTENT: [Checkboxes]
SUMMARY: [Context]
AGENT TASKS: [Tasks]
=== END SYSTEM HANDOFF ===
```

**Spec:** `docs/CHATGPT_COMMS_PROTOCOL_v0.5.md`

**Delivery:** User copy-paste (v0.5), future automation (v1+)

---

### Claude CLI ↔ GitHub Copilot Agent

**Protocol:** Git repo as shared state

**Mechanisms:**
- Commits and pushes (Claude CLI → repo → GitHub Copilot Agent)
- Pull requests (GitHub Copilot Agent → repo → Claude CLI)
- Issues and comments (both agents can read/write)
- `ai/coordination/messages.jsonl` (coordination file)

**Async by default:** Each agent sees other's work via repo updates

---

### Task Queue System

**Shared:** `ai/tasks/*.json`

Both Claude CLI and GitHub Copilot Agent can:
- Read tasks from queue
- Create new tasks
- Update task status
- Mark tasks complete

**Format:**
```json
{
  "id": "task_123",
  "title": "Task description",
  "origin": "chatgpt|claude_cli|github_copilot_agent",
  "status": "pending|in_progress|completed",
  "files": ["list", "of", "files"],
  "context": {}
}
```

---

## Relationship to Existing Documentation

This protocol is a **thin glue layer** connecting existing documentation:

### Related Protocols
- **CHATGPT_COMMS_PROTOCOL_v0.5.md** - How ChatGPT hands off work via SYSTEM HANDOFF blocks
- **CHATGPT_COMMS_PROTOCOL_v1_ideas.md** - Future automation ideas

### Related Architecture
- **.claude/AI_COORDINATION_ARCHITECTURE.md** - Original coordination architecture (if present)
- **.claude/MCP_ARCHITECTURE_CORRECTION.md** - MCP (Model Context Protocol) details
- **ai/coordination/messages.jsonl** - Real-time agent coordination

### Integration Points
- **ai/tasks/*.json** - Shared task queue
- **ai/coordination/** - Agent coordination files
- **.claude/instructions.md** - Claude CLI directives

**Key point:** AI_AGENT_LINK_PROTOCOL_v0.1 doesn't replace these - it links them into a coherent multi-agent system.

---

## Agent Registry

Machine-readable registry: `ai/agents/AGENTS_REGISTRY_v0.1.json`

Contains:
- Agent IDs
- Roles
- Handoff protocols
- Input/output channels

**Purpose:** Single source of truth for "what agents exist and how they work"

Future tools can parse this registry to:
- Validate handoffs
- Route tasks appropriately
- Generate coordination diagrams
- Audit agent interactions

---

## Design Principles

### 1. Use Best Tool for Job
- ChatGPT for research → Use ChatGPT
- Claude CLI for implementation → Use Claude CLI
- GitHub features needed → Use GitHub Copilot Agent

### 2. No Rigid Hierarchies
- Agents are peers with different strengths
- No "boss agent" coordinating others
- Repo is shared source of truth

### 3. Explicit Handoffs
- Clear protocols (SYSTEM HANDOFF, tasks, PRs)
- User facilitates handoffs (v0.1)
- Future: automation (v1+)

### 4. Documentation Over Code
- v0.1 is purely documentation
- No runtime dependencies
- Safe to evolve

### 5. Backward Compatible
- Doesn't break existing workflows
- Additive only
- Can be ignored if not needed

---

## Current Limitations (v0.1)

**This is documentation only:**
- ✅ Defines agents and protocols
- ✅ Explains communication flows
- ❌ No code enforcement
- ❌ No automatic routing
- ❌ User still copies/pastes

**Why that's okay:**
- Solves immediate confusion about agent roles
- Provides foundation for future automation
- Low risk - pure documentation
- Can iterate based on actual usage

---

## Future Evolution

### v0.2 - Enhanced Documentation
- Add examples of successful multi-agent workflows
- Document common patterns
- Troubleshooting guide

### v1.0 - Light Automation
- Parser validates SYSTEM HANDOFF format
- Auto-route based on TARGET field
- Task queue integration

### v2.0 - Full Integration
- Direct agent-to-agent communication
- Automatic handoff routing
- Coordination without user intervention

**See:** `docs/CHATGPT_COMMS_PROTOCOL_v1_ideas.md` for automation roadmap

---

## For Agents Reading This

### If you're ChatGPT:
- Your role: Research and design
- Output format: SYSTEM HANDOFF blocks
- Target: Claude CLI (primary) or GitHub Copilot Agent (secondary)
- You don't touch the repo - you hand off to agents that do

### If you're Claude CLI:
- Your role: Primary implementer
- Input: SYSTEM HANDOFF blocks, tasks, direct requests
- Output: Commits, docs, task updates
- You have full repo access - use it

### If you're GitHub Copilot Agent:
- Your role: GitHub-native helper
- Input: Issues, PRs, AI-intake, optionally SYSTEM HANDOFF
- Output: PRs, commits, status comments
- You work through GitHub features

### If you're a future agent:
- Read this protocol to understand the system
- Add yourself to `AGENTS_REGISTRY_v0.1.json`
- Follow existing handoff protocols
- Document your role clearly

---

## Summary

**Three agents, clear roles, explicit handoffs:**

| Agent | Role | Input | Output |
|-------|------|-------|--------|
| ChatGPT | Research/Design | User conversation | SYSTEM HANDOFF |
| Claude CLI | Implementation | SYSTEM HANDOFF, tasks | Commits, docs |
| GitHub Copilot Agent | GitHub helper | Issues, PRs, AI-intake | PRs, comments |

**Handoff protocol:** SYSTEM HANDOFF v0.5 (documented in `CHATGPT_COMMS_PROTOCOL_v0.5.md`)

**Shared state:** Git repo, `ai/tasks/`, `ai/coordination/`

**Philosophy:** Use best AI for each job, no rigid hierarchies, explicit handoffs.

---

**Status:** v0.1 live - documentation layer active, no runtime changes

**Next:** Use it, learn from it, evolve to v0.2 based on experience
