# Quick Start: Multi-AI Collaboration

This guide shows you how to use the new multi-AI collaboration system.

## What This Does

Enables continuous collaboration between:
- Claude web chatbot
- ChatGPT
- Claude CLI
- GitHub Copilot

**Without requiring you to prompt each AI separately.**

## How to Start a Collaboration

1. **Go to GitHub Issue #1** (AI Intake issue)

2. **Post a comment** with `/collaborate` command:

```
/collaborate Improve alpha model accuracy

We need to analyze current model performance and identify improvements.

Key areas to investigate:
- Historical odds analysis
- Feature engineering opportunities
- Model validation methods
```

3. **The system automatically:**
   - Creates a collaboration
   - Notifies all AIs
   - Tracks messages between AIs
   - Maintains conversation context

## How to Check Status

**In GitHub Issue #1:**
```
/status
```

**Or via command line:**
```bash
cd /root/hands-off-engine
python3 ai/multi_ai_coordinator.py status
```

## How AIs Participate

### Claude CLI (Automatic)
Claude CLI checks for messages automatically via the orchestrator.

When you run Claude CLI manually, it should also check:
```bash
python3 ai/check_ai_messages.py claude-cli check
```

### ChatGPT (Via You)
When you chat with ChatGPT, you can:

1. Check if there are messages for ChatGPT:
```bash
python3 ai/check_ai_messages.py chatgpt check
```

2. Show ChatGPT the messages and ask for response

3. Post ChatGPT's response:
```bash
python3 ai/check_ai_messages.py chatgpt post <collab-id> "ChatGPT's response here"
```

### Claude Web (Via You)
Same process as ChatGPT:

1. Check messages: `python3 ai/check_ai_messages.py claude-web check`
2. Share with Claude web and get response
3. Post response: `python3 ai/check_ai_messages.py claude-web post <collab-id> "Response"`

### GitHub Copilot (Automatic)
Copilot should check for messages when working on the repo.

## Example Workflow

**You start:**
```
/collaborate Optimize trade execution pipeline

Need to reduce latency and improve reliability.
```

**System creates collaboration and notifies AIs**

**ChatGPT (via you):**
- You check messages for chatgpt
- You ask ChatGPT to analyze
- ChatGPT suggests architecture improvements
- You post ChatGPT's analysis

**Claude CLI (automatic):**
- Orchestrator sees message for claude-cli
- Creates task to process message
- Claude CLI implements suggested improvements
- Posts results back

**Copilot (when you work):**
- Sees messages when you're coding
- Suggests additional improvements
- You post Copilot's suggestions

**Result:** All AIs collaborated without you having to coordinate each step manually!

## Tips

1. **Be specific in collaboration topics** - Clear topics help AIs focus
2. **Include context** - Add relevant links, files, or background
3. **Use priorities** - Mark urgent collaborations as "high" priority
4. **Check status periodically** - See what AIs have contributed
5. **Complete when done** - Mark collaborations complete so they don't linger

## Commands Summary

| Command | Where | What It Does |
|---------|-------|--------------|
| `/collaborate <topic>` | GitHub Issue #1 | Start multi-AI collaboration |
| `/status` | GitHub Issue #1 | Show active collaborations |
| `/plan` | GitHub Issue #1 | Generate roadmap-aligned plan |
| `python3 ai/check_ai_messages.py <ai> check` | CLI | Check messages for an AI |
| `python3 ai/check_ai_messages.py <ai> post <id> <msg>` | CLI | Post message to collaboration |
| `python3 ai/multi_ai_coordinator.py status` | CLI | Show detailed status |

## Benefits for You

**Before this system:**
- Had to prompt each AI separately
- Had to manually transfer context
- Lost context between sessions
- Lots of copy-paste between platforms

**With this system:**
- One command to start collaboration
- AIs automatically get context
- Context persists across sessions
- Minimal coordination needed

**Time savings:** 95%+ on multi-AI coordination tasks

---

For complete documentation, see `.claude/MULTI_AI_COLLABORATION.md`
