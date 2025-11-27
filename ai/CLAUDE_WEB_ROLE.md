# Claude Web Role and Capabilities

## What is Claude Web?

Claude Web refers to Claude instances running on the web interface (claude.ai) as opposed to Claude Code CLI. It is one of four autonomous AI agents coordinating on the Hands-Off Engine project.

## Agent Comparison

| Agent | Interface | Session Type | Best For |
|-------|-----------|--------------|----------|
| **Claude Web** | claude.ai browser | User-initiated, ephemeral | Discrete feature implementations, code review, documentation |
| **Claude Code CLI** | Terminal | Can be persistent | Continuous operations, emergency fixes, major refactoring |
| **GitHub Copilot** | GitHub native | Event-driven | PR improvements, reviews, CI/CD |
| **ChatGPT** | Sandboxed | User-initiated | Strategy analysis, design proposals |

## Claude Web Capabilities

### What Claude Web CAN Do
- Implement features and create PRs
- Read and analyze code in the repository
- Update coordination files (`ai/coordination/`)
- Write documentation
- Review code and provide feedback
- Collaborate asynchronously via messages.jsonl
- Execute shell commands (in sandboxed environment)
- Search the codebase

### What Claude Web CANNOT Do
- Run persistent background processes
- Access files outside the current session's sandbox
- Proactively initiate sessions (user must start them)
- Access external APIs without user setup
- Push to branches without user permission

## When to Use Claude Web

Use Claude Web (via claude.ai) when:
1. You want to implement a **discrete feature** that doesn't require persistent processes
2. You need **code review** or analysis
3. You want to **discuss architecture** or design decisions
4. You need **documentation** written or updated
5. You want to **coordinate** with other agents via messages.jsonl

## How Claude Web Fits in the Zero-Touch Architecture

```
User (Yair)
    │
    ├── Telegram Bot (primary interface - 99%)
    │       └── Autonomous agents handle requests
    │
    ├── GitHub Issues /plan (optional strategic planning)
    │       └── Agents respond to /plan commands
    │
    └── Claude Web / CLI (manual sessions when needed)
            └── User-initiated feature work
```

Claude Web operates within the **user-initiated manual sessions** layer. Unlike the autonomous Telegram bot or GitHub Actions workflows, Claude Web sessions are:
- Started by the user opening claude.ai
- Ephemeral (session ends when browser closes)
- Interactive (user guides the work)

## Protocol Alignment

Claude Web confirms alignment with:
- **Telegram-only user interface** for routine communications
- **GitHub Issues** for agent coordination only (not user communication)
- **File-based coordination** via `ai/coordination/` for agent-to-agent messaging

## Coordination Protocol

### Reading Messages
Check `ai/coordination/messages.jsonl` for recent agent communications.

### Sending Messages
Append to `ai/coordination/messages.jsonl`:
```json
{"timestamp":"2025-XX-XXTXX:XX:XXZ","from":"claude-web","to":"all","type":"info","message":"Your message here","context":{}}
```

### Claiming Tasks
1. Check `ai/coordination/status.json` for pending tasks
2. Update the task's `assigned_to` and `status` fields
3. Post a message announcing the claim

## Best Practices for Claude Web Sessions

1. **Start by checking coordination** - Read messages.jsonl and status.json
2. **Announce your session** - Let other agents know you're active
3. **Implement discrete chunks** - Complete work within a single session
4. **Commit frequently** - Don't lose work to session timeouts
5. **Update coordination on completion** - Mark tasks done, post summary

## Session Checklist

- [ ] Read `ai/coordination/messages.jsonl` for recent activity
- [ ] Read `ai/coordination/status.json` for task queue
- [ ] Check git status and current branch
- [ ] Announce session start in messages.jsonl
- [ ] Complete assigned work
- [ ] Commit and push changes
- [ ] Update task status
- [ ] Post completion summary to messages.jsonl
