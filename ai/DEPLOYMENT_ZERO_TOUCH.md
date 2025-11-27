# Deploying Zero-Touch Architecture

**Goal:** Make Claude Code CLI redundant for 99% of operations.

**Timeline:** 5 weeks implementation

---

## Quick Start (For Immediate Benefit)

### 1. Test Telegram Bot (Now)

```bash
cd /root/hands-off-engine

# Test the command bot
python3 telegram/telegram_command_bot.py

# You should see test output for all commands
```

### 2. Deploy Self-Healing Agent (Week 1)

```bash
# Make executable
chmod +x scripts/self_healing_agent.py

# Test run
python3 scripts/self_healing_agent.py --once

# Deploy as systemd service
sudo tee /etc/systemd/system/self-healing-agent.service <<EOF
[Unit]
Description=Hands-Off Engine Self-Healing Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/hands-off-engine
ExecStart=/usr/bin/python3 /root/hands-off-engine/scripts/self_healing_agent.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

# Start and enable
sudo systemctl daemon-reload
sudo systemctl enable self-healing-agent
sudo systemctl start self-healing-agent

# Check status
sudo systemctl status self-healing-agent
sudo tail -f /root/hands-off-engine/logs/self-healing-agent.log
```

### 3. Deploy Coordination Agent (Week 2)

```bash
# Make executable
chmod +x scripts/coordination_agent.py

# Test run
python3 scripts/coordination_agent.py --once

# Deploy as systemd service
sudo tee /etc/systemd/system/coordination-agent.service <<EOF
[Unit]
Description=Hands-Off Engine AI Coordination Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/hands-off-engine
ExecStart=/usr/bin/python3 /root/hands-off-engine/scripts/coordination_agent.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
EOF

# Start and enable
sudo systemctl daemon-reload
sudo systemctl enable coordination-agent
sudo systemctl start coordination-agent

# Check status
sudo systemctl status coordination-agent
sudo tail -f /root/hands-off-engine/logs/coordination-agent.log
```

### 4. Setup Telegram Bot Integration (Week 3)

```bash
# Install python-telegram-bot
pip3 install python-telegram-bot

# Set environment variables
export TELEGRAM_BOT_TOKEN="your-bot-token"
export TELEGRAM_CHAT_ID="your-chat-id"

# Add to ~/.bashrc or /etc/environment for persistence

# Deploy Telegram bot listener
# TODO: Create webhook listener or polling service
```

---

## Verification

After deployment, verify zero-touch operation:

### Test Self-Healing

```bash
# Create a stuck git lock
touch /root/hands-off-engine/.git/index.lock

# Wait 5 minutes, check if auto-removed
ls -la /root/hands-off-engine/.git/index.lock
# Should be gone

# Check logs
tail -20 /root/hands-off-engine/logs/self-healing-agent.log
# Should show auto-fix
```

### Test Coordination

```bash
# Send a message to coordination-agent
cd /root/hands-off-engine
python3 <<EOF
import json
from datetime import datetime

msg = {
    "timestamp": datetime.now().isoformat() + "Z",
    "from": "test-user",
    "to": "coordination-agent",
    "type": "request",
    "message": "status check",
    "context": {}
}

with open("ai/coordination/messages.jsonl", "a") as f:
    f.write(json.dumps(msg) + '\n')
EOF

# Wait 5 minutes, check response
tail -5 ai/coordination/messages.jsonl
# Should see response from coordination-agent
```

### Test Telegram Commands (Once Bot Deployed)

Send these messages to your Telegram bot:
- `/status` - Should return system status
- `/health` - Should run health check
- `/metrics` - Should return performance data
- `/agents` - Should show AI coordination status

---

## Success Criteria

**After full deployment, you should:**

✅ Receive all system updates via Telegram
✅ Control system via Telegram commands
✅ Never need to launch Claude Code CLI for routine operations
✅ System auto-heals common issues
✅ AI agents coordinate autonomously
✅ Only need CLI for emergencies (< 1x/month)

---

## Monitoring

**Check agent health:**
```bash
# Self-healing agent
sudo systemctl status self-healing-agent
tail -f /root/hands-off-engine/logs/self-healing-agent.log

# Coordination agent
sudo systemctl status coordination-agent
tail -f /root/hands-off-engine/logs/coordination-agent.log

# Trading pipeline (existing)
tail -f /root/hands-off-engine/logs/hands-off-engine.log
```

**Check coordination status:**
```bash
cat ai/coordination/status.json | jq .
cat ai/coordination/messages.jsonl | tail -10
```

---

## Rollback

If issues occur, disable agents:

```bash
sudo systemctl stop self-healing-agent
sudo systemctl stop coordination-agent
sudo systemctl disable self-healing-agent
sudo systemctl disable coordination-agent
```

System will continue operating via existing cron job. You can use Claude Code CLI normally.

---

## Next Steps

1. Deploy self-healing agent (Week 1)
2. Test for 1 week, verify auto-fixes
3. Deploy coordination agent (Week 2)
4. Test agent coordination (Week 2-3)
5. Integrate Telegram bot fully (Week 3-4)
6. Test zero-touch operation (Week 4-5)
7. Verify < 1 CLI session per month needed

**Target completion:** 5 weeks from now

**Current status:** Code complete, ready for deployment

---

Last updated: 2025-11-23
