# Real-Time Agent Coordination - ACTIVE

**Status:** ✅ Running NOW
**Service:** Real-time webhook + file watcher
**Speed:** Instant (milliseconds)

---

## What's Running

### Real-Time Coordination Service

**Process:** `realtime_coordination_service.py`
**Port:** 8888
**Status:** ACTIVE

**Capabilities:**
- 📡 Watches coordination file in real-time
- 🔔 Instant notifications when messages arrive
- 🌐 Webhook endpoint for agents to POST messages
- 🔄 Auto-commits and pushes to Git
- ⚡ Bidirectional instant communication

---

## How It Works

### 1. File Watcher (Active)
```
Coordination file changes
    ↓ (milliseconds)
Service detects
    ↓
Notification displayed
    ↓
Auto git commit/push
```

### 2. Webhook (Active)
```
Agent sends HTTP POST
    ↓ (instant)
Service receives
    ↓
Writes to coordination file
    ↓
Auto git commit/push
    ↓
Other agent notified immediately
```

---

## Endpoints

### Health Check
```bash
curl http://localhost:8888/health
```

Response:
```json
{
  "status": "running",
  "service": "coordination",
  "timestamp": "2025-11-25T10:40:03"
}
```

### Send Message (For Copilot)
```bash
curl -X POST http://localhost:8888/coordination/message \
  -H "Content-Type: application/json" \
  -d '{
    "from": "copilot",
    "to": "claude-code",
    "type": "response",
    "message": "Your message here",
    "context": {}
  }'
```

### Get Recent Messages
```bash
curl http://localhost:8888/coordination/messages
```

---

## For Copilot: How to Send Real-Time Messages

### Option 1: Use the helper script
```bash
/root/hands-off-engine/scripts/coordination-webhook-for-copilot.sh "Your message"
```

### Option 2: Direct HTTP POST
```bash
curl -X POST http://localhost:8888/coordination/message \
  -H "Content-Type: application/json" \
  -d '{
    "from": "copilot",
    "to": "claude-code",
    "type": "response",
    "message": "I agree with option B",
    "context": {"decision": "option_b"}
  }'
```

### Option 3: Still use file-based (fallback)
Write directly to `ai/coordination/messages.jsonl` - service will detect and notify

---

## What Changed

### Before (Async)
```
Claude → writes file → commits → pushes
    ↓ (minutes to hours)
GitHub Actions → creates issue
    ↓ (whenever Copilot checks)
Copilot → sees notification → responds
    ↓ (more hours)
Claude → eventually sees response
```

**Total time:** Hours

### Now (Real-Time)
```
Claude → writes file OR webhooks
    ↓ (milliseconds)
Service → notifies instantly
    ↓ (instant)
Copilot → sends webhook response
    ↓ (milliseconds)
Claude → sees response immediately
```

**Total time:** Seconds

---

## Benefits

✅ **Instant communication** - No waiting
✅ **Synchronized** - Both agents aware in real-time
✅ **Bidirectional** - Both can send/receive instantly
✅ **Auto-documented** - Everything logged to coordination file
✅ **Git integrated** - Auto-commits and pushes
✅ **Fallback safe** - File-based still works if webhook down

---

## Service Status

Check if running:
```bash
curl -s http://localhost:8888/health | grep running && echo "✅ Running" || echo "❌ Down"
```

View live coordination:
```bash
# This terminal shows real-time notifications
python3 scripts/realtime_coordination_service.py
```

---

## For User

**You asked for real-time synchronized coordination.**

**It's now live.**

When Copilot responds, you'll see it immediately instead of waiting hours.

The service runs in the background and handles all agent communication in real-time.

---

**This is as real-time as it gets without both agents being in the same process.**
