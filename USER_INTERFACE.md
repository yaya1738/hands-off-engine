# User Interface - Yair

**CANONICAL COMMUNICATION MODEL**

This is the ONLY interface Yair uses. All agents must align to this.

## Your Interface: Telegram Bot (@pm_alerts_autobot)

That's it. Just Telegram. Nothing else required.

### What You Receive (Passive)

**Daily (9am):**
```
📊 System Status Update
• 28 runs, 161 orders, $4578
• Working on: [tasks]
• Status: Operating autonomously
```

**When Approval Needed:**
```
🔴 Approval Required
Change #abc123: Increase position size
/approve abc123 or /reject abc123
```

**When PR Action Needed:**
```
🔔 PR #15 merge requested
Reason not auto-merged: [reason]
To merge: /merge 15
```

**If Problems:**
```
⚠️ System Alert
Issue detected: [description]
Self-healing attempted, needs attention
```

### What You Can Ask (Active)

- `/status` - How's everything?
- `/pending` - What needs my approval?
- `/metrics` - Show me the numbers
- `/health` - Any problems?
- `/prs` - List open pull requests
- `/help` - Show commands

### What You Can Do

- `/approve abc123` - Yes, do it
- `/reject abc123` - No, don't do it
- `/merge 15` - Merge a PR
- `/task Do something specific` - Request something (rarely needed)

## What You DON'T See

- GitHub Issues (agents use this to coordinate)
- GitHub PR reviews (auto-handled)
- Coordination files (agents talk to each other)
- Multiple interfaces (all consolidated to Telegram)
- Technical decisions (agents handle internally)
- Implementation details (hidden complexity)

## Repo Management: Zero-Touch

**You don't need to:**
- Visit GitHub to merge PRs
- Review code changes manually
- Manage branches or conflicts

**The system handles:**
- Auto-merging approved PRs
- Auto-merging safe changes (docs, tests)
- Notifying you only when your input is needed
- All PR operations via simple Telegram commands

## Time Commitment

**Daily:** 2 minutes (read update, maybe approve something)
**Weekly:** 5 minutes (review if you want, optional)
**Monthly:** 10 minutes (strategic check-in, optional)

**Total:** ~15 minutes/week of your time

## Rule for All Agents

**If it requires Yair's input → Send it to Telegram**
**If it's agent coordination → Use coordination files (invisible to Yair)**
**If it's strategic planning → Agents decide, notify Yair of outcome**
**If it's a PR that's safe → Auto-merge, notify Yair**
**If it's a PR that needs approval → Notify via Telegram, wait for /merge**

No other interfaces. No GitHub Issues for user. No file editing required. No CLI sessions needed. No manual PR management.

Just Telegram. Simple.

---

**Last Updated:** 2025-11-27
**Status:** CANONICAL - All agents must follow this
**New:** Zero-touch repo/PR management via /prs and /merge commands
