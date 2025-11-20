# AI Integration Infrastructure

This directory contains configuration and task definitions for AI-driven work on the Hands-Off Engine.

## Structure

- **`/tasks/*.json`** - Individual task definitions for AI agents
- **`/state/knowledge.json`** (repo root) - Central knowledge base with primary docs and bootstrap instructions

## How to Use

### For AI Agents/Tools

1. Read `/state/knowledge.json` to get the primary status doc
2. Read the primary status doc (currently: `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`)
3. For specific tasks, load the task JSON from `/ai/tasks/*.json`
4. Include files listed in `context_files` as required reading

### Task JSON Format

See `EXAMPLE_TASK.json` for the template. Key fields:

- `task_id` - Unique identifier
- `description` - What needs to be done
- `context_files` - Files the AI must read (should always include the research report)
- `instructions` - Specific steps or requirements
- `status` - Current state (pending/in_progress/completed/template)

This makes the "standard opening instruction" part of the **data model**, not just natural language conventions.
