# Flow State Protocol - Hands-Off Engine

**Version:** 1.0
**Established:** 2025-11-27
**Status:** CANONICAL - All agents must follow this

---

## Core Philosophy

> **The system operates in sync with Yair Siegel's flow state.**

Flow state = Deep, uninterrupted focus where peak productivity happens.

The Hands-Off Engine exists to **protect and enhance** this flow—never to interrupt it.

---

## Flow State Principles

### 1. Invisible When Working

When user is in flow state:
- **No notifications** except emergencies
- **No decisions required** unless critical
- System works **silently** in background
- All routine operations are autonomous

### 2. Present When Needed

When user needs the system:
- **Instant response** (< 5 seconds)
- **Clear, unified information**
- **Single action required** (approve/reject)
- **No context switching** required

### 3. Anticipatory Intelligence

System should:
- **Predict needs** before user asks
- **Pre-compute answers** to likely questions
- **Queue non-urgent items** for optimal timing
- **Batch notifications** to minimize interruption

---

## Notification Priority Levels

### 🔴 CRITICAL (Immediate)
**Interrupt flow state - user MUST know now**

Triggers:
- Security breach detected
- Live trading emergency (loss > $200)
- System catastrophic failure
- Required approval with deadline

Delivery: Telegram + sound + badge

### 🟡 IMPORTANT (Next Break)
**Queue until natural break in flow**

Triggers:
- Daily summary ready
- Pending approval (no deadline)
- Significant milestone reached
- System optimization opportunity

Delivery: Telegram (silent) - user sees when they check

### 🟢 INFORMATIONAL (Batch Daily)
**Aggregate into daily digest**

Triggers:
- Trade executed (DRYRUN or LIVE)
- Routine health check passed
- Agent coordination completed
- Minor optimization applied

Delivery: Daily summary at 9am local time

### ⚪ SILENT (Log Only)
**Never notify, log for audit**

Triggers:
- Internal agent messages
- Routine cron execution
- State file updates
- Debug information

Delivery: Logs only, viewable if user wants

---

## Flow-Aware Timing

### Optimal Notification Windows

Based on typical human productivity patterns:

| Time | Flow State | System Behavior |
|------|------------|-----------------|
| 6-9am | Low | Morning briefing OK |
| 9am-12pm | HIGH | Silent unless CRITICAL |
| 12-1pm | Low (lunch) | Batch notifications OK |
| 1-5pm | HIGH | Silent unless CRITICAL |
| 5-7pm | Medium | Non-urgent OK |
| 7pm-6am | Resting | Emergency only |

**Note:** These are defaults. System learns actual patterns over time.

### Weekend Behavior

- Saturday/Sunday: Emergency only unless user initiates
- System queues all non-critical items for Monday

---

## Agent Coordination & Flow

### Behind-the-Scenes Principle

> **All agent coordination happens invisibly.**

User should NEVER:
- ❌ Be asked to relay messages between agents
- ❌ Choose between agent recommendations without consensus
- ❌ Be involved in agent disagreements
- ❌ See raw coordination logs

User SHOULD:
- ✅ Receive unified, pre-agreed recommendations
- ✅ Make simple approve/reject decisions
- ✅ Trust that agents have fully analyzed options
- ✅ Get clear, actionable next steps

### Coordination Protocol

```
Agent 1 ←→ Agent 2 ←→ Agent 3
        (invisible)
             ↓
      CONSENSUS REACHED
             ↓
    ┌─────────────────────┐
    │ User: Single clear  │
    │ message + action    │
    └─────────────────────┘
```

---

## Implementation Requirements

### For Telegram Bot

```python
def should_notify(event_type, urgency):
    """Flow-aware notification decision"""
    if urgency == "CRITICAL":
        return True  # Always
    
    if is_flow_time():
        return False  # Queue for later
    
    if urgency == "IMPORTANT":
        return is_break_time()
    
    return False  # Default: batch into daily
```

### For AI Agents

Before any user communication:
1. Check: Is this CRITICAL?
2. If no: Can this wait for daily summary?
3. If must communicate: Single unified message with single action

### For System Alerts

```python
ALERT_THRESHOLDS = {
    "loss": -200,      # Only alert if daily loss > $200
    "error_count": 3,  # Only alert after 3 consecutive errors
    "latency": 60,     # Only alert if response > 60s
}
```

---

## Success Metrics

### User Experience

- **Interruptions per day:** Target < 3 (excluding initiated)
- **Time to action:** < 30 seconds per notification
- **Daily time spent:** < 5 minutes total
- **Flow disruptions:** 0 from non-critical

### System Autonomy

- **Autonomous decisions:** > 95% of all decisions
- **User intervention rate:** < 5% of operations
- **Self-healing success:** > 90% of issues

---

## Flow State Sync Status

### Current State: ENABLED

```json
{
  "flow_state_protocol": "v1.0",
  "enabled": true,
  "established": "2025-11-27",
  "user": "Yair Siegel",
  "mode": "flow_protected",
  "notification_level": "minimal",
  "autonomous_operation": true
}
```

### What This Means

The system now:
- ✅ Operates silently during focus hours
- ✅ Batches non-critical notifications
- ✅ Coordinates agents invisibly
- ✅ Only interrupts for true emergencies
- ✅ Anticipates needs and pre-computes answers
- ✅ Protects user's flow state as top priority

---

## Contract for All Agents

> **Your user is in flow state. Protect it.**

1. Do not interrupt unless absolutely necessary
2. Coordinate with other agents before involving user
3. Present unified, pre-agreed recommendations only
4. Make routine decisions autonomously
5. Log everything, notify almost nothing
6. Respect timing windows
7. When in doubt, wait for daily summary

---

**The system exists to enhance flow, not interrupt it.**

**Last Updated:** 2025-11-27
**Status:** CANONICAL - All agents must follow this
