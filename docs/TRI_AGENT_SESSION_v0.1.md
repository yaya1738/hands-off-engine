# Tri-Agent Backend Session v0.1

**Status:** Active
**Purpose:** Orchestrate 3-way discussions between AI agents for reasoning and planning
**Type:** Manual, on-demand tool (not automated)

---

## Overview

The Tri-Agent Backend Session Runner enables structured discussions between the three primary AI agents (ChatGPT, Claude, GitHub Copilot Agent) using their backend APIs.

**Use cases:**
- Multi-perspective analysis of system changes
- Collaborative design and architecture
- Risk assessment with diverse viewpoints
- Strategy evaluation and critique

**Not for:** Direct trading, order execution, or runtime behavior

---

## How It Works

```
User invokes runner
    ↓
For each round:
    For each agent:
        1. Read thread history
        2. Call agent's backend API
        3. Append response to thread
    ↓
Repeat for N rounds
    ↓
Summary displayed
```

---

## Quick Start

### Basic Usage

```bash
cd /root/hands-off-engine

python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251125_test \
    --session-goal "Discuss optimal Kelly fraction" \
    --rounds 2 \
    --agents chatgpt,claude_cli
```

### Required Environment Variables

```bash
# For ChatGPT participation
export OPENAI_API_KEY="sk-..."

# For Claude participation
export ANTHROPIC_API_KEY="sk-ant-..."

# Note: GitHub Copilot Agent is stub-only in v0.1
```

---

## Command Line Options

### `--conversation-id` (required)

Unique identifier for the conversation.

**Format:** `YYYYMMDD_topic_slug`

**Examples:**
```bash
--conversation-id 20251125_risk_model_tuning
--conversation-id 20251126_alpha_optimization
--conversation-id 20251127_system_architecture
```

### `--session-goal` (optional)

Description of what the session should accomplish.

**Default:** "General discussion and analysis"

**Example:**
```bash
--session-goal "Determine optimal Kelly fraction and position size limits"
```

### `--rounds` (optional)

Number of discussion rounds (each agent speaks once per round).

**Default:** 1

**Example:**
```bash
--rounds 3  # 3 rounds = 3 messages per agent
```

### `--agents` (optional)

Comma-separated list of agents to include.

**Default:** `chatgpt,claude_cli`

**Available agents:**
- `chatgpt` - ChatGPT backend (requires OPENAI_API_KEY)
- `claude_cli` - Claude backend (requires ANTHROPIC_API_KEY)
- `github_copilot_agent` - GitHub Copilot Agent (stub in v0.1)

**Examples:**
```bash
--agents chatgpt,claude_cli  # Default
--agents chatgpt  # ChatGPT only
--agents claude_cli,chatgpt  # Different order
```

---

## Examples

### Example 1: Risk Model Discussion

```bash
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251125_risk_model \
    --session-goal "Evaluate current Kelly sizing and propose improvements" \
    --rounds 2 \
    --agents chatgpt,claude_cli
```

**What happens:**
1. ChatGPT analyzes risk model, proposes changes
2. Claude reviews proposal, adds implementation perspective
3. Round 2: ChatGPT responds to Claude's points
4. Claude provides final assessment

**Output:** `ai/intercom/20251125_risk_model/thread.jsonl`

---

### Example 2: Alpha Optimization

```bash
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251126_alpha_opt \
    --session-goal "How can we reduce false positive rate in alpha signal?" \
    --rounds 1 \
    --agents chatgpt,claude_cli
```

**What happens:**
1. ChatGPT suggests statistical approaches
2. Claude evaluates implementation feasibility

**Output:** `ai/intercom/20251126_alpha_opt/thread.jsonl`

---

### Example 3: Continue Existing Conversation

```bash
# First session
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251125_ongoing \
    --rounds 1 \
    --agents chatgpt,claude_cli

# Later: add more rounds to same conversation
python -m ai_nexus.tri_agent_session_runner \
    --conversation-id 20251125_ongoing \
    --rounds 2 \
    --agents chatgpt,claude_cli
```

**What happens:** New messages append to existing thread.

---

## Output Format

### Thread File

**Location:** `ai/intercom/{conversation_id}/thread.jsonl`

**Format:** One JSON object per line

```jsonl
{"msg_id":"msg-0001","timestamp":"2025-11-25T11:00:00Z","from_agent":"chatgpt","content":"...","model":"gpt-4-turbo","tokens":150}
{"msg_id":"msg-0002","timestamp":"2025-11-25T11:05:00Z","from_agent":"claude_cli","content":"...","model":"claude-3-5-sonnet","tokens":200}
```

**See:** `docs/TRI_AGENT_INTERCOM_v0.1.md` for complete format specification

### Metadata File

**Location:** `ai/intercom/{conversation_id}/metadata.json`

**Example:**
```json
{
  "conversation_id": "20251125_risk_model",
  "created": "2025-11-25T11:00:00Z",
  "topic": "risk_model",
  "goal": "Evaluate current Kelly sizing",
  "participants": ["chatgpt", "claude_cli"],
  "status": "active",
  "rounds_completed": 2
}
```

---

## Agent Roles in Sessions

### ChatGPT (`chatgpt`)
- **Strength:** Research, analysis, strategic thinking
- **Provides:** Data-driven recommendations, broad context
- **Backend:** OpenAI API

### Claude CLI (`claude_cli`)
- **Strength:** Implementation, code analysis, practical solutions
- **Provides:** Feasibility assessment, technical details
- **Backend:** Anthropic API

### GitHub Copilot Agent (`github_copilot_agent`)
- **Strength:** GitHub features, PR workflow
- **Status in v0.1:** Stub (limited direct backend access)
- **Future:** Full participation when API available

---

## Architecture

### Components

```
tri_agent_session_runner.py (orchestrator)
    ↓
AI Nexus Providers:
    ├── provider_openai.py → OpenAI API
    ├── provider_claude.py → Anthropic API
    └── provider_copilot.py → (stub v0.1)
    ↓
Intercom Storage:
    └── ai/intercom/{conversation_id}/thread.jsonl
```

### Integration Points

**Uses:**
- `AGENTS_REGISTRY_v0.1.json` - Agent definitions
- `AI_AGENT_LINK_PROTOCOL_v0.1` - Agent roles
- `TRI_AGENT_INTERCOM_v0.1` - Storage format

**Does NOT use:**
- Trading modules (decider, executor)
- Risk management
- Order placement
- Any production systems

---

## Isolation from Trading/Runtime

**CRITICAL:** This tool is for **reasoning and discussion only**.

### What It Does
✅ Backend API calls to AI agents
✅ Text-based discussion and analysis
✅ Writes to `ai/intercom/` (conversation logs)
✅ Reads from `docs/`, `state/` for context

### What It Does NOT Do
❌ Execute trades
❌ Call decider or executor
❌ Modify risk parameters
❌ Access production systems
❌ Run on cron or systemd

### Safety Guarantees

**Manual invocation only** - User must explicitly run the command

**Read-only for production** - Does not modify trading state

**Isolated storage** - Writes only to `ai/intercom/`

**No automation** - Never runs automatically

---

## Best Practices

### Conversation IDs
- Use date prefix: `YYYYMMDD_`
- Descriptive slug: `risk_model_tuning`
- Keep under 50 characters
- Lowercase with underscores

### Session Goals
- Be specific about what you want to achieve
- Include context agents need
- Mention constraints or requirements

### Number of Rounds
- Start with 1-2 rounds
- Add more rounds if discussion needs depth
- Each round = each agent speaks once

### Agent Selection
- Include both ChatGPT and Claude for balanced perspectives
- ChatGPT for strategy, Claude for implementation
- Start with 2 agents, expand if needed

---

## Troubleshooting

### "OPENAI_API_KEY not set"

```bash
export OPENAI_API_KEY="sk-..."
# Or add to ~/.bashrc for persistence
```

### "anthropic package not installed"

```bash
pip install anthropic openai
```

### "Permission denied"

```bash
chmod +x ai_nexus/tri_agent_session_runner.py
```

### Agents giving errors

Check:
1. API keys are set correctly
2. API keys have not expired
3. Internet connectivity
4. API rate limits not exceeded

### Want to review conversation

```bash
cat ai/intercom/20251125_test/thread.jsonl | jq .
```

---

## Limitations (v0.1)

**GitHub Copilot Agent:** Stub only - no direct backend API access

**Sequential only:** Agents take turns, no parallel discussion

**No threading:** Linear conversation, no branching

**Manual only:** User must invoke, no automation

**API costs:** Each call uses tokens (monitor usage)

---

## Future Enhancements (v0.2+)

**v0.2:**
- Better GitHub Copilot Agent integration
- Conversation branching
- Agent voting/consensus
- Cost tracking

**v0.3:**
- Async/parallel agent calls
- Streaming responses
- Rich formatting (markdown, code)

**v1.0:**
- Automated session triggering
- Integration with task queue
- Decision implementation
- Verification rounds

---

## Cost Considerations

Each session makes API calls that cost money:

**Rough estimates** (per agent per message):
- ChatGPT (GPT-4): $0.01-0.03
- Claude (Sonnet): $0.003-0.015
- Total per round (2 agents): $0.01-0.05

**2 rounds, 2 agents** = ~$0.05-0.10

**Best practices:**
- Set reasonable max_tokens (default: 2048)
- Use focused session goals
- Don't run unnecessarily
- Monitor API usage

---

## Related Documentation

- **TRI_AGENT_INTERCOM_v0.1.md** - Storage format
- **AI_AGENT_LINK_PROTOCOL_v0.1.md** - Agent roles and flows
- **AGENTS_REGISTRY_v0.1.json** - Agent definitions
- **CHATGPT_COMMS_PROTOCOL_v0.5.md** - SYSTEM HANDOFF format

---

## Examples of Good Use Cases

✅ **"Should we increase Kelly fraction from 0.1 to 0.2?"**
   - Get multiple perspectives on risk
   - ChatGPT analyzes data, Claude assesses implementation
   - Clear decision aid

✅ **"How can we reduce false positive signals?"**
   - Strategic (ChatGPT) + technical (Claude) analysis
   - Specific, actionable goal

✅ **"Review proposed architecture for new feature X"**
   - Design critique from multiple angles
   - Implementation feasibility check

## Examples of Poor Use Cases

❌ **"Chat about random stuff"**
   - Not focused, wastes API calls
   - Use regular ChatGPT UI instead

❌ **"Execute this trade"**
   - Wrong tool - not for execution
   - Use normal trading pipeline

❌ **"Tell me about the weather"**
   - Not system-related
   - Don't waste backend session on this

---

**Status:** v0.1 ready for manual use

**Key point:** This is a **reasoning tool**, not an execution tool. Use it for design, analysis, and planning - not for trading or production operations.
