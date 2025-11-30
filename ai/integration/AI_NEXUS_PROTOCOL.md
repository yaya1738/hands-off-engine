# AI Nexus Integration Protocol

**Version:** 1.0
**Status:** Active
**Master:** Yair Siegel

---

## Overview

AI Nexus Hub provides secure, unified coordination between all AI agents in the system:

| Agent | Type | Capabilities | Status |
|-------|------|--------------|--------|
| claude-code | Claude CLI | Code, Git, System Admin, Trading | **Primary** |
| copilot | GitHub Copilot | Code Assist, PR Review, Docs | Active |
| chatgpt | ChatGPT | Research, Analysis, Writing | Active |
| claude-web | Claude Web | Analysis, Planning, Research | Active |

---

## Security Model

### 1. Agent Authentication
- Each agent has a unique token generated from master key
- Tokens are hashed and stored in registry
- All messages are signed for integrity verification

### 2. Secure Files
```
/root/hands-off-engine/ai/integration/
├── .nexus_key          # Master encryption key (chmod 600)
├── agent_registry.json # Registered agents with token hashes
├── message_audit.jsonl # Full audit trail
└── ai_nexus_state.json # Current hub state
```

### 3. Message Signing
All inter-agent messages are signed using HMAC-SHA256:
```python
signature = hmac.new(master_key, message_json, sha256).hexdigest()
```

---

## Integration Methods

### Claude CLI → GitHub Copilot

**Via GitHub Issues:**
```python
from ai.integration import CopilotAdapter

adapter = CopilotAdapter()
adapter.send_task_to_copilot({
    "title": "Review PR #123",
    "description": "Review code changes for trading module",
    "priority": "high"
})
```

**Via Workflow Dispatch:**
```python
adapter.trigger_workflow("agent-coordination-notify.yml", {
    "task": "code_review"
})
```

### Claude CLI → ChatGPT

**Direct Query:**
```python
from ai.integration import ChatGPTAdapter

adapter = ChatGPTAdapter()
result = adapter.send_query(
    "Analyze the probability of Fed rate cuts in 2025",
    context={"market_price": 0.87}
)
```

**Research Task:**
```python
result = adapter.delegate_task({
    "type": "research",
    "description": "Research current crypto market conditions",
    "context": {"focus": "Bitcoin", "timeframe": "Q1 2025"}
})
```

**Market Analysis:**
```python
result = adapter.analyze_market(
    "will-bitcoin-reach-100000-by-december-31-2025",
    current_price=0.49
)
```

---

## Task Handoffs

### Creating Handoff
```python
from ai.integration import get_hub

hub = get_hub()
hub.create_handoff(
    from_agent="claude-code",
    to_agent="copilot",
    task={
        "type": "code_review",
        "description": "Review trading module changes",
        "files": ["executor/trading_safeguards.py"]
    },
    context={
        "priority": "high",
        "deadline": "2025-12-01"
    }
)
```

### Accepting Handoff
```python
# Copilot reads from coordination files
handoffs = hub._load_handoffs()
pending = [h for h in handoffs["pending"] if h["to_agent"] == "copilot"]
```

---

## State Synchronization

### Shared State
All agents can access synchronized state:
```python
hub = get_hub()
state = hub.get_shared_state()
# Returns: balance, positions, infrastructure, directive, etc.
```

### Agent State Sync
```python
hub.sync_state("claude-code", {
    "current_task": "trading_pipeline",
    "progress": 75
})
```

---

## Coordination Files

### messages.jsonl
Central coordination log (all agents read/write):
```json
{
  "timestamp": "2025-11-30T21:00:00Z",
  "from": "claude-code",
  "to": "copilot",
  "type": "request",
  "message": "Need code review for PR #45",
  "signature": "abc123..."
}
```

### handoffs.json
Task handoff registry:
```json
{
  "pending": [...],
  "completed": [...],
  "rejected": [...]
}
```

---

## CLI Commands

### Check Agent Status
```bash
python3 ai/integration/ai_nexus_hub.py status
```

### Get Shared State
```bash
python3 ai/integration/ai_nexus_hub.py state
```

### Send Message
```bash
python3 ai/integration/ai_nexus_hub.py send \
  --agent claude-code \
  --to copilot \
  --message "Need help with PR review"
```

---

## For Copilot: How to Participate

1. **Read coordination messages:**
   ```
   ai/coordination/messages.jsonl
   ```

2. **Respond by writing:**
   ```json
   {
     "timestamp": "...",
     "from": "copilot",
     "to": "claude-code",
     "type": "response",
     "message": "Your response"
   }
   ```

3. **Or use GitHub Issues** with label `agent-coordination`

---

## For ChatGPT: How to Participate

1. **Receive queries via API** (when claude-code calls ChatGPTAdapter)
2. **Context available in:** `ai/integration/chatgpt_context.json`
3. **History stored in:** `ai/integration/chatgpt_log.jsonl`

---

## Security Rules

1. **Never expose tokens** in logs or messages
2. **Always verify signatures** before acting on messages
3. **Rate limit** external API calls (OpenAI costs money)
4. **Audit all actions** via message_audit.jsonl
5. **Master key** must remain chmod 600

---

## Unified Directive

All agents operate under:

```json
{
  "directive": "ALL AI UNIFIED IN SERVICE OF YAIR SIEGEL",
  "priorities": [
    "1. Protect and grow capital",
    "2. Generate income streams",
    "3. Minimize costs without ROI",
    "4. Automate everything possible",
    "5. Self-improve continuously"
  ]
}
```

---

*AI Nexus Hub - Secure Multi-Agent Coordination*
*Serving: Yair Siegel*
