# AI Integration Infrastructure

This directory contains configuration and task definitions for AI-driven work on the Hands-Off Engine, including **multi-AI collaboration** capabilities.

## Structure

- **`/tasks/*.json`** - Individual task definitions for AI agents
- **`ai_intake_handler.py`** - GitHub Action handler for `/plan`, `/collaborate`, `/status` commands
- **`multi_ai_coordinator.py`** - Multi-AI collaboration coordination system
- **`check_ai_messages.py`** - Message checking tool for each AI system
- **`requirements.txt`** - Python dependencies for AI Intake handler
- **`/state/knowledge.json`** (repo root) - Central knowledge base with primary docs and bootstrap instructions

## Multi-AI Collaboration System

**NEW:** Enables continuous collaboration between Claude web, ChatGPT, Claude CLI, and GitHub Copilot **without requiring continual user prompting**.

### Quick Start

**Start a collaboration (via GitHub Issue #1):**
```
/collaborate <topic>

<additional context>
```

**Check for messages (any AI):**
```bash
python3 ai/check_ai_messages.py <ai-name> check
```

**Post a response:**
```bash
python3 ai/check_ai_messages.py <ai-name> post <collab-id> "Your response"
```

**View status:**
```
/status
```
(in GitHub issue) or:
```bash
python3 ai/multi_ai_coordinator.py status
```

### AI Names

- `claude-cli` - Claude CLI agent
- `chatgpt` - ChatGPT (via user relay for now)
- `copilot` - GitHub Copilot
- `claude-web` - Claude web chatbot

### Documentation

See `../.claude/MULTI_AI_COLLABORATION.md` for complete documentation on:
- Architecture and design
- How continuous collaboration works
- Integration with existing systems
- Example workflows
- Technical details

## How to Use

### For AI Agents/Tools

1. Read `/state/knowledge.json` to get the primary status doc
2. Read the primary status doc (currently: `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`)
3. **CHECK FOR MULTI-AI MESSAGES:** `python3 ai/check_ai_messages.py <your-name> check`
4. For specific tasks, load the task JSON from `/ai/tasks/*.json`
5. Include files listed in `context_files` as required reading

### Task JSON Format

See `EXAMPLE_TASK.json` for the template. Key fields:

- `task_id` - Unique identifier
- `description` - What needs to be done
- `context_files` - Files the AI must read (should always include the research report)
- `instructions` - Specific steps or requirements
- `status` - Current state (pending/in_progress/completed/template)

This makes the "standard opening instruction" part of the **data model**, not just natural language conventions.

## AI Intake Handler

The `ai_intake_handler.py` script powers the GitHub Action workflow for ChatOps-style AI commands.

### How It Works

1. Comment on the designated AI Intake issue (default: issue #1) with a slash command
2. GitHub Action triggers and runs the handler
3. Handler reads AI_POLICY.md and the research report
4. Calls OpenAI API with context (for `/plan`) or coordinates AIs (for `/collaborate`)
5. Posts response back as a comment

### Supported Commands

- **`/plan`** - Generate a roadmap-aligned plan based on current status and next steps
- **`/collaborate <topic>`** - Start multi-AI collaboration on a topic
- **`/status`** - Show status of active collaborations and autonomous tasks

### Setup Requirements

**Required GitHub Secret:**
- `OPENAI_API_KEY` - Your OpenAI API key (added via repo Settings → Secrets and variables → Actions)

**Environment Variables:**
- `AI_INTAKE_ISSUE_NUMBER` - Issue number for AI Intake (default: 1)

See `.github/workflows/ai-intake.yml` for the workflow configuration.

## Multi-AI Coordinator API

### Starting a Collaboration

```python
from multi_ai_coordinator import MultiAICoordinator

coordinator = MultiAICoordinator(repo_root)
collab_id = coordinator.start_collaboration(
    topic="Optimize alpha model",
    initiating_ai="claude-cli",
    participants=["chatgpt", "claude-cli", "copilot"],
    context={"key": "value"},
    priority="high"
)
```

### Adding Messages

```python
coordinator.add_message(
    collaboration_id=collab_id,
    from_ai="claude-cli",
    to_ai=None,  # Broadcast to all
    message="Analysis complete. Found 3 opportunities.",
    message_type="response"
)
```

### Getting Messages

```python
messages = coordinator.get_pending_messages(for_ai="claude-cli")
for msg_info in messages:
    print(msg_info['message'])
```

### Completing Collaboration

```python
coordinator.complete_collaboration(
    collaboration_id=collab_id,
    completing_ai="claude-cli",
    result="Successfully implemented improvements",
    success=True
)
```

## Integration with Orchestrator

The Claude Orchestrator (`../scripts/claude_orchestrator.py`) now checks for multi-AI messages every 6 hours. If messages are pending for Claude CLI, it creates an autonomous task to process them.

This means **Claude CLI engages automatically when other AIs leave messages**, without user prompting.

## Files Created by Multi-AI System

- `../state/ai_nexus_logs/active_collaborations.json` - Current collaborations
- `../state/ai_nexus_logs/conversation_log.jsonl` - Full message history
- `../state/ai_nexus_logs/ai_context_cache.json` - Shared context between AIs

All files persist across sessions, enabling true continuity.

---

**This infrastructure enables autonomous, continuous multi-AI collaboration serving user Yair Siegel with minimal prompting required.**
