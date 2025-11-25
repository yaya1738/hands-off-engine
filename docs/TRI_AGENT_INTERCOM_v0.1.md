# Tri-Agent Intercom v0.1

**Status:** Active
**Purpose:** Storage format for 3-way backend agent discussions
**Location:** `ai/intercom/`

---

## Overview

The Tri-Agent Intercom provides a structured storage format for conversations between the three primary AI agents (ChatGPT, Claude CLI, GitHub Copilot Agent) when running in backend session mode.

**Not for:** Direct user interaction (use SYSTEM HANDOFF for that)
**For:** Agent-to-agent reasoning, discussion, critique, and planning

---

## Storage Structure

### Directory Layout

```
ai/intercom/
├── {conversation_id}/
│   ├── thread.jsonl          # Main conversation thread
│   ├── metadata.json          # Optional conversation metadata
│   └── artifacts/             # Optional: files referenced in discussion
└── README.md                  # This file or usage guide
```

### Conversation ID Format

Convention: `YYYYMMDD_topic_slug`

Examples:
- `20251125_risk_model_tuning`
- `20251126_alpha_optimization`
- `20251127_system_architecture`

---

## Thread Format (`thread.jsonl`)

Each line is a JSON object representing one message in the conversation.

### Required Fields

```json
{
  "msg_id": "msg-0001",
  "timestamp": "2025-11-25T11:30:00Z",
  "from_agent": "chatgpt | claude_cli | github_copilot_agent",
  "content": "Message content here..."
}
```

### Recommended Fields (v0.1)

```json
{
  "msg_id": "msg-0001",
  "timestamp": "2025-11-25T11:30:00Z",
  "from_agent": "chatgpt",
  "topic": "risk_model_tuning",
  "kind": "proposal",
  "content": "I suggest we adjust the Kelly sizing...",
  "references": [
    "docs/RISK_MODEL.md",
    "state/performance_metrics.jsonl"
  ],
  "model": "gpt-4-turbo",
  "tokens": 150
}
```

### Field Descriptions

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `msg_id` | Yes | string | Unique message ID (e.g., `msg-0001`) |
| `timestamp` | Yes | ISO 8601 | When message was created |
| `from_agent` | Yes | enum | One of: `chatgpt`, `claude_cli`, `github_copilot_agent` |
| `content` | Yes | string | The actual message text |
| `topic` | No | string | Short slug for topic |
| `kind` | No | enum | Message type: `proposal`, `critique`, `plan`, `note`, `question`, `answer` |
| `references` | No | array | Files/docs mentioned |
| `model` | No | string | AI model used (for debugging) |
| `tokens` | No | number | Token count (for cost tracking) |

---

## Message Kinds

**proposal** - Suggests a change or new approach
**critique** - Analyzes or finds issues with something
**plan** - Outlines steps to implement something
**note** - General observation or context
**question** - Asks for input/clarification
**answer** - Responds to a question

---

## Metadata Format (`metadata.json`)

Optional file describing the conversation:

```json
{
  "conversation_id": "20251125_risk_model_tuning",
  "created": "2025-11-25T11:00:00Z",
  "topic": "Risk Model Parameter Tuning",
  "goal": "Determine optimal Kelly fraction and position size limits",
  "participants": ["chatgpt", "claude_cli", "github_copilot_agent"],
  "status": "active | completed | archived",
  "rounds_completed": 3,
  "outcome": "Agreed on Kelly 0.25, max position $200"
}
```

---

## Usage Examples

### Reading a Thread

```python
import json
from pathlib import Path

thread_file = Path("ai/intercom/20251125_risk_model/thread.jsonl")

messages = []
with open(thread_file) as f:
    for line in f:
        messages.append(json.loads(line))

# Get last 5 messages
recent = messages[-5:]

# Get all messages from ChatGPT
chatgpt_msgs = [m for m in messages if m['from_agent'] == 'chatgpt']
```

### Writing a Message

```python
import json
from datetime import datetime
from pathlib import Path

message = {
    "msg_id": f"msg-{len(messages)+1:04d}",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "from_agent": "claude_cli",
    "content": "I've analyzed the proposal...",
    "kind": "critique",
    "references": ["state/polymarket-model.json"]
}

thread_file = Path("ai/intercom/20251125_risk_model/thread.jsonl")
with open(thread_file, 'a') as f:
    f.write(json.dumps(message) + '\n')
```

---

## Design Principles

### 1. Simple JSONL Format
- One message per line
- Easy to append
- Easy to parse
- Human-readable

### 2. Schema-Light (v0.1)
- Only 4 required fields
- Other fields optional
- Can evolve without breaking

### 3. File-Based
- No database needed
- Easy to version control
- Easy to inspect/debug
- Works in Termux

### 4. Conversation-Scoped
- Each conversation is isolated
- Easy to archive/delete
- No cross-contamination

---

## Best Practices

### Conversation IDs
- Use date prefix for chronology
- Use descriptive slug
- Keep under 50 characters
- Lowercase with underscores

### Message Content
- Be concise but complete
- Include reasoning
- Reference specific files/data
- Mark uncertain claims

### References
- Use repo-relative paths
- Verify files exist before referencing
- Keep list short (< 10 items)

### Thread Management
- Don't edit existing messages
- Append only
- Archive completed conversations
- Keep threads focused (< 100 messages)

---

## Integration with Other Systems

### AI Agent Link Protocol
- Intercom complements SYSTEM HANDOFF
- SYSTEM HANDOFF: User → Agent
- Intercom: Agent ↔ Agent ↔ Agent

### Agents Registry
- Agent IDs must match `AGENTS_REGISTRY_v0.1.json`
- Use: `chatgpt`, `claude_cli`, `github_copilot_agent`

### Tri-Agent Session Runner
- Reads/writes thread.jsonl
- Orchestrates multi-round discussions
- See: `docs/TRI_AGENT_SESSION_v0.1.md`

---

## Limitations (v0.1)

**No real-time sync** - File-based, manual refresh

**No authentication** - All agents trusted

**No message editing** - Append-only by convention

**No threading** - Linear conversation only

**No reactions/votes** - Simple messages only

These are acceptable for v0.1. Future versions can add features as needed.

---

## Example Thread

```jsonl
{"msg_id":"msg-0001","timestamp":"2025-11-25T11:00:00Z","from_agent":"claude_cli","content":"Starting discussion on risk model tuning. Current Kelly fraction is 0.1, seems too conservative.","kind":"proposal"}
{"msg_id":"msg-0002","timestamp":"2025-11-25T11:05:00Z","from_agent":"chatgpt","content":"Analyzed historical data. With current edge (6-8%), Kelly 0.1 is indeed conservative. Could safely increase to 0.20-0.25 based on backtest results.","kind":"critique","references":["state/performance_metrics.jsonl"]}
{"msg_id":"msg-0003","timestamp":"2025-11-25T11:10:00Z","from_agent":"github_copilot_agent","content":"Agree with increase, but recommend gradual rollout. Start at 0.15, monitor for 1 week, then 0.20.","kind":"plan"}
{"msg_id":"msg-0004","timestamp":"2025-11-25T11:15:00Z","from_agent":"claude_cli","content":"Good approach. Will implement staged rollout: 0.15 (week 1), 0.20 (week 2), evaluate before going to 0.25.","kind":"answer"}
```

---

**Status:** v0.1 specification complete and ready for use

**See also:** `docs/TRI_AGENT_SESSION_v0.1.md` for session runner documentation
