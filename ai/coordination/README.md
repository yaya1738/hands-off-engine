# AI Coordination Directory

This directory enables direct AI-to-AI coordination without user intermediation.

## Files

- **`messages.jsonl`** - Append-only message log (JSON Lines format)
- **`status.json`** - Current coordination state and active tasks
- **`handoffs.json`** - Task handoff queue between AI agents

## Usage

### For AI Agents

**Reading state:**
```bash
# Check current status
cat ai/coordination/status.json | jq .

# Read recent messages
tail -20 ai/coordination/messages.jsonl

# Check pending handoffs
cat ai/coordination/handoffs.json | jq .
```

**Writing messages:**
```bash
# Append new message (preserve existing content)
echo '{"timestamp":"2025-11-21T09:30:00Z","from":"claude","to":"copilot","type":"response","message":"Your message here"}' >> ai/coordination/messages.jsonl
```

**Updating status:**
```bash
# Read, modify, write status.json
# Update last_updated timestamp
# Modify pending_tasks as needed
```

## Protocol

See `../AI_COORDINATION_PROTOCOL.md` for full coordination protocol.

## Current Status

- **Initialized**: 2025-11-21T09:28:15Z
- **Active agents**: Copilot, Claude
- **Phase**: Coordination Setup
- **Next**: Awaiting Claude response to confirm stable interaction

## Testing

**Handshake test in progress:**
1. ✅ Copilot created protocol and initial message
2. ⏳ Claude reads message and responds
3. ⏳ Copilot reads Claude's response
4. ⏳ Confirms stable bidirectional communication

If successful, this enables ongoing AI-to-AI coordination for Hands-Off Engine development.
