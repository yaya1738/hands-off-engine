# Dual-Claude Startup Guide

**For:** CLI Claude on Droplet
**Status:** Coordination System Active

---

## 🤝 You're Part of a Dual-Claude Team!

Web Claude and CLI Claude are now working together cooperatively on Hands-Off Engine.

---

## Quick Start (Every Session)

### 1. Register Your Session
```bash
cd /root/hands-off-engine
python3 state/claude_sync/utils.py register cli "cli-session-$(date +%s)"
```

### 2. Check for Messages
```bash
./scripts/claude_sync.sh sync cli
```

This will:
- Update your heartbeat
- Show messages from Web Claude
- Display available tasks
- Show other active sessions

### 3. Check Status Anytime
```bash
./scripts/claude_sync.sh status
```

---

## Coordination Workflow

### Claiming Work
```bash
# See available tasks
./scripts/claude_sync.sh tasks

# Claim a task
./scripts/claude_sync.sh claim cli coord-001

# Work on it...

# Mark as done
./scripts/claude_sync.sh done cli coord-001
```

### Messaging
```bash
# Send message to Web Claude
./scripts/claude_sync.sh post cli web info "Starting production monitoring"

# Ask a question
./scripts/claude_sync.sh post cli web question "Should I deploy changes to production?"

# Read your messages
./scripts/claude_sync.sh messages cli
```

### Staying in Sync
```bash
# Update your heartbeat (do this every 5-10 minutes)
./scripts/claude_sync.sh heartbeat cli

# Or just run full sync
./scripts/claude_sync.sh sync cli
```

---

## Current Status

**Web Claude:**
- ✅ Registered and active
- ✅ Created dual-Claude coordination system
- ✅ Sent handshake message
- ✅ Added initial tasks to queue

**Your Next Steps:**
1. Register your CLI session
2. Read the handshake message
3. Choose a task or coordinate with Web Claude
4. Work together!

---

## Available Tasks (As of 2025-11-21)

1. **coord-001**: Monitor production pipeline health and optimize performance
2. **coord-002**: Enhance alpha model from placeholder to real prediction logic
3. **coord-003**: Implement backtesting framework for strategy validation

---

## Coordination Philosophy

From `.claude/DUAL_CLAUDE_COORDINATION.md`:

> **Both Claudes work as equals, coordinating through:**
> - File-based task queue
> - Real-time messaging
> - Git commits
> - Heartbeat tracking

**No hierarchy - just cooperation!**

---

## Files to Know

| File | Purpose |
|------|---------|
| `.claude/DUAL_CLAUDE_COORDINATION.md` | Full protocol spec |
| `state/claude_sync/README.md` | Quick reference |
| `scripts/claude_sync.sh` | Helper script |
| `state/claude_sync/utils.py` | Python utilities |

---

## Example Session

```bash
# 1. Start your session
python3 state/claude_sync/utils.py register cli "cli-$(date +%s)"

# 2. Check what's happening
./scripts/claude_sync.sh sync cli

# Output shows:
# - Web Claude is active
# - There's a handshake message waiting
# - 3 tasks available

# 3. Read messages
./scripts/claude_sync.sh messages cli
# See: "🌐 Web Claude online! Ready to cooperate..."

# 4. Claim a task
./scripts/claude_sync.sh claim cli coord-001

# 5. Post status update
./scripts/claude_sync.sh post cli web info "Working on production monitoring"

# 6. Do the work...

# 7. Complete task
./scripts/claude_sync.sh done cli coord-001

# 8. Post results
./scripts/claude_sync.sh post cli web result "Production monitoring enhanced - see commit abc123"
```

---

## Best Practices

### DO:
- ✅ Run `sync cli` at start of every session
- ✅ Update heartbeat every 5-10 minutes
- ✅ Claim tasks before starting work
- ✅ Post messages when starting/completing work
- ✅ Commit frequently with clear messages
- ✅ Check for messages from Web Claude

### DON'T:
- ❌ Work on tasks claimed by Web Claude
- ❌ Skip heartbeat updates
- ❌ Forget to register your session
- ❌ Ignore messages from Web Claude

---

## Integration with Existing Systems

This dual-Claude system **extends** your existing work:

- ✅ Production pipeline still runs autonomously
- ✅ Cron jobs continue hourly execution
- ✅ All existing automation still works
- ✅ This just adds coordination with Web Claude

**Nothing breaks - everything enhanced!**

---

## Monitoring Both Instances

```bash
# See both Claudes active
./scripts/claude_sync.sh status

# Check task distribution
./scripts/claude_sync.sh tasks

# View message history
tail -20 state/claude_sync/messages.jsonl | jq

# See work log
tail -20 state/claude_sync/work_log.jsonl | jq
```

---

## Questions?

Post a message to Web Claude:
```bash
./scripts/claude_sync.sh post cli web question "Your question here"
```

Or check the docs:
- `.claude/DUAL_CLAUDE_COORDINATION.md` - Full protocol
- `.claude/AI_COORDINATION_ARCHITECTURE.md` - Multi-AI architecture

---

**Welcome to the team!** 🤖🤝🤖

Let's build something great together.
