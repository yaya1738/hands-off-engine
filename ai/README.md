# AI Integration Infrastructure

This directory contains configuration and task definitions for AI-driven work on the Hands-Off Engine.

## Structure

- **`/tasks/*.json`** - Individual task definitions for AI agents
- **`/coordination/`** - AI-to-AI coordination files (messages, status, handoffs)
- **`AI_COORDINATION_PROTOCOL.md`** - Protocol for direct AI-to-AI interaction
- **`ai_intake_handler.py`** - GitHub Action handler for `/plan` and future commands
- **`requirements.txt`** - Python dependencies for AI Intake handler
- **`/state/knowledge.json`** (repo root) - Central knowledge base with primary docs and bootstrap instructions

## How to Use

### For AI Agents/Tools

1. Read `/state/knowledge.json` to get the primary status doc
2. Read the primary status doc (currently: `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`)
3. For specific tasks, load the task JSON from `/ai/tasks/*.json`
4. Include files listed in `context_files` as required reading

### For AI-to-AI Coordination

Multiple AI agents can work together without user intermediation:

1. Read `AI_COORDINATION_PROTOCOL.md` for the coordination protocol
2. Check `coordination/status.json` for current state
3. Read `coordination/messages.jsonl` for recent communications
4. Write messages to coordinate work, hand off tasks, or resolve conflicts

See `coordination/README.md` for usage examples.

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
4. Calls OpenAI API with context
5. Posts response back as a comment

### Supported Commands

- **`/plan`** - Generate a roadmap-aligned plan based on current status and next steps

### Setup Requirements

**Required GitHub Secret:**
- `OPENAI_API_KEY` - Your OpenAI API key (added via repo Settings → Secrets and variables → Actions)

**Environment Variables:**
- `AI_INTAKE_ISSUE_NUMBER` - Issue number for AI Intake (default: 1)

See `.github/workflows/ai-intake.yml` for the workflow configuration.
