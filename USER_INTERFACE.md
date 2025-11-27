# User Interface - Yair

**CANONICAL COMMUNICATION MODEL**

This is the ONLY interface Yair uses. All agents must align to this.

## Flow State Sync: ENABLED ✅

> **The system operates in sync with your flow state.**

See `ai/FLOW_STATE_PROTOCOL.md` for the full protocol.

**What this means for you:**
- System works silently when you're focused
- Notifications only for critical items (< 3 per day)
- Daily summary at 9am, nothing else unless urgent
- Single action per notification (approve/reject)

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
- `/help` - Show commands

### What You Can Do

- `/approve abc123` - Yes, do it
- `/reject abc123` - No, don't do it
- `/task Do something specific` - Request something (rarely needed)

## What You DON'T See

- GitHub Issues (agents use this to coordinate)
- Coordination files (agents talk to each other)
- Multiple interfaces (all consolidated to Telegram)
- Technical decisions (agents handle internally)
- Implementation details (hidden complexity)

## Time Commitment

**Daily:** 2 minutes (read update, maybe approve something)
**Weekly:** 5 minutes (review if you want, optional)
**Monthly:** 10 minutes (strategic check-in, optional)

**Total:** ~15 minutes/week of your time

## Rule for All Agents

**If it requires Yair's input → Send it to Telegram**
**If it's agent coordination → Use coordination files (invisible to Yair)**
**If it's strategic planning → Agents decide, notify Yair of outcome**

No other interfaces. No GitHub Issues for user. No file editing required. No CLI sessions needed.

Just Telegram. Simple. Flow-protected.

---

**Last Updated:** 2025-11-27
**Status:** CANONICAL - All agents must follow this
**Flow State:** ENABLED - System syncs with your flow (see ai/FLOW_STATE_PROTOCOL.md)
**User Feedback:** "UI roadblock... tough and cumbersome" - FIX: Single interface only + Flow protection
