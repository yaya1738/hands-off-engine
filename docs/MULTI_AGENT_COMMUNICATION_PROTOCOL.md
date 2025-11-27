# Multi-Agent Communication Protocol v1.0

This document defines the infrastructure for collaboration between GitHub Copilot,
Claude, and other AI resources in the Hands-Off Engine.

---

## Overview

The Hands-Off Engine uses multiple AI agents working autonomously:

| Agent | Role | Access |
|-------|------|--------|
| GitHub Copilot | GitHub-native helper, PR reviews, code generation | GitHub API, repo via PRs |
| Claude Code | Primary repo implementer, CLI operations | Full repo access |
| ChatGPT | Research, strategy, architecture | Via SYSTEM HANDOFF blocks |
| Claude Web | Research assistance, analysis | Via user relay |

---

## Communication Channels

### 1. File-Based Coordination (Primary)

**Location:** `ai/coordination/`

| File | Purpose |
|------|---------|
| `messages.jsonl` | Agent-to-agent messages in JSON Lines format |
| `status.json` | Current system state and task assignments |
| `handoffs.json` | Task handoff tracking between agents |

**Message Format:**
```json
{
  "timestamp": "2025-11-27T12:00:00Z",
  "from": "copilot",
  "to": "claude-code",
  "type": "request|response|info",
  "message": "Message content",
  "context": {
    "additional": "data"
  }
}
```

### 2. GitHub Actions Workflows

**Workflow:** `.github/workflows/agent-coordination-notify.yml`

Triggers:
- Push to `ai/coordination/messages.jsonl`
- Push to `ai/coordination/status.json`
- Manual workflow_dispatch

Actions:
- Creates/updates GitHub Issue labeled `agent-coordination`
- Sends repository_dispatch for Copilot activation
- Posts coordination messages as issue comments

### 3. AI Intake Handler

**Workflow:** `.github/workflows/ai-intake.yml`
**Handler:** `ai/ai_intake_handler.py`

Commands (posted as issue comments):
- `/plan` - Generate roadmap-aligned plan
- Future: `/status`, `/risk`, `/alpha`, `/todo`

### 4. AI Nexus Backend Sessions

**Location:** `ai_nexus/`

The tri-agent session runner enables direct backend communication:
```bash
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id my_session \
    --session-goal "Discuss topic" \
    --agents chatgpt,claude_cli
```

---

## Agent-Specific Integration

### GitHub Copilot Integration

**Provider:** `ai_nexus/provider_copilot.py`

Copilot integrates via:
1. **GitHub Issues/PRs** - Primary interaction surface
2. **Coordination files** - Async message passing
3. **GitHub Actions** - Automated workflow triggers

**Posting a message as Copilot:**
```python
from ai_nexus.provider_copilot import post_copilot_response

post_copilot_response(
    message="Response content",
    response_type="response",
    context={"task_id": "xyz"}
)
```

**Checking integration status:**
```python
from ai_nexus.provider_copilot import get_copilot_integration_status

status = get_copilot_integration_status()
# Returns: autonomous_mode, total_messages, capabilities
```

### Claude Integration

**Provider:** `ai_nexus/provider_claude.py`

Claude integrates via:
1. **Direct API calls** - When ANTHROPIC_API_KEY is set
2. **CLI operations** - Full repo access for implementation
3. **Coordination files** - Message passing with other agents

### ChatGPT Integration

**Provider:** `ai_nexus/provider_openai.py`

ChatGPT integrates via:
1. **Direct API calls** - When OPENAI_API_KEY is set
2. **SYSTEM HANDOFF blocks** - Structured task handoff format
3. **AI Intake workflow** - For `/plan` commands

---

## Inter-Agent Communication Flows

### Flow 1: Copilot ↔ Claude via Coordination Files

```
Copilot writes to messages.jsonl
    ↓
Push triggers agent-coordination-notify.yml
    ↓
Workflow creates/updates GitHub Issue
    ↓
Claude reads messages.jsonl (via repo access)
    ↓
Claude writes response to messages.jsonl
    ↓
Push triggers workflow again
    ↓
Copilot sees notification
```

### Flow 2: ChatGPT → Claude via SYSTEM HANDOFF

```
ChatGPT produces SYSTEM HANDOFF block
    ↓
User pastes into Claude session OR GitHub Issue
    ↓
Claude implements AGENT TASKS
    ↓
Claude commits changes to repo
```

### Flow 3: GitHub Actions Automation

```
Push to ai/coordination/*
    ↓
agent-coordination-notify.yml triggers
    ↓
Creates/updates agent-coordination Issue
    ↓
repository_dispatch sent
    ↓
Copilot workflows can trigger
```

### Flow 4: Tri-Agent Backend Session

```
Session started with chatgpt,claude_cli
    ↓
ChatGPT provides analysis
    ↓
Claude provides implementation recommendations
    ↓
(Copilot can be included for GitHub-specific tasks)
    ↓
Session logged to ai/intercom/
```

---

## Quick Reference

### For Copilot

1. Check `ai/coordination/status.json` for assigned tasks
2. Read `ai/coordination/messages.jsonl` for pending requests
3. Write responses to `messages.jsonl` using standard format
4. GitHub Actions will notify other agents automatically

### For Claude

1. Read `.claude/instructions.md` for context
2. Check `ai/coordination/messages.jsonl` for agent messages
3. Implement tasks and commit to repo
4. Write coordination messages for status updates

### For New Agents

1. Add entry to `ai/agents/AGENTS_REGISTRY_v0.1.json`
2. Create provider in `ai_nexus/provider_<name>.py`
3. Use coordination files for communication
4. Follow message format specification

---

## Configuration

### Environment Variables

| Variable | Used By | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | ChatGPT | API access |
| `ANTHROPIC_API_KEY` | Claude | API access |
| `GITHUB_TOKEN` | Workflows | GitHub API access |

### Files

| Path | Purpose |
|------|---------|
| `ai/coordination/status.json` | System state |
| `ai/coordination/messages.jsonl` | Agent messages |
| `ai/agents/AGENTS_REGISTRY_v0.1.json` | Agent registry |
| `.github/copilot-instructions.md` | Copilot context |
| `.claude/instructions.md` | Claude context |

---

## Version History

- **v1.0** (2025-11-27): Initial unified protocol
  - Copilot provider v0.2 with coordination integration
  - Documented all communication flows
  - Added agent-specific integration guides
