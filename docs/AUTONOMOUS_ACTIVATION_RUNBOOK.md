# Autonomous Activation Runbook

**Purpose:** Step-by-step guide to activate documented autonomous features  
**Target:** Close gap between documentation and implementation  
**Prerequisite:** Read `AUTONOMOUS_IMPLEMENTATION_STATUS.md`

---

## Overview

This runbook activates the autonomous architecture documented in:
- `docs/claude/AUTONOMOUS_OPERATION.md`
- `docs/AUTONOMOUS_BOTTLENECKS_RESOLVED.md`
- `ai/ZERO_TOUCH_ARCHITECTURE.md`

**Current State:** Code exists, services not running  
**Target State:** 24/7 autonomous operation with Telegram control

---

## Prerequisites Check

Before starting, verify:

```bash
# 1. Repository location
cd /opt/hands-off-engine || cd ~/hands-off-engine
pwd  # Should show hands-off-engine directory

# 2. Python 3 available
python3 --version  # Should be 3.8+

# 3. Scripts executable
ls -l scripts/*.py scripts/*.sh | grep -v "^-rwx"  # Should be empty

# 4. Log directory writable
sudo mkdir -p /var/log/hands-off
sudo chmod 777 /var/log/hands-off
ls -ld /var/log/hands-off  # Should show drwxrwxrwx

# 5. State directory exists
mkdir -p state logs config
ls -ld state logs config  # Should all exist
```

---

## Phase 1: Core Services Activation

### 1.1 Self-Healing Agent

**Purpose:** 24/7 monitoring and auto-fix of common issues

**Steps:**

```bash
# Test script locally first
python3 scripts/self_healing_agent.py --test

# Expected: Health check runs, reports system status

# If test succeeds, create systemd service
sudo tee /etc/systemd/system/self-healing-agent.service > /dev/null << 'EOF'
[Unit]
Description=Hands-Off Engine Self-Healing Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hands-off-engine
ExecStart=/usr/bin/python3 /opt/hands-off-engine/scripts/self_healing_agent.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/hands-off/self-healing.log
StandardError=append:/var/log/hands-off/self-healing-error.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable self-healing-agent
sudo systemctl start self-healing-agent

# Verify running
sudo systemctl status self-healing-agent
# Should show: Active (running)

# Monitor logs
tail -f /var/log/hands-off/self-healing.log
# Should see health check cycles every 5 minutes
```

**Validation:**
- [ ] Service status shows "Active (running)"
- [ ] Log shows health checks every 5 minutes
- [ ] No error messages in error log
- [ ] State file created: `state/self_healing_state.json`

### 1.2 Coordination Agent

**Purpose:** Process AI-to-AI messages and coordinate tasks

**Steps:**

```bash
# Test script locally
python3 scripts/coordination_agent.py --test

# Expected: Reads coordination files, processes messages

# Create systemd service
sudo tee /etc/systemd/system/coordination-agent.service > /dev/null << 'EOF'
[Unit]
Description=Hands-Off Engine AI Coordination Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hands-off-engine
ExecStart=/usr/bin/python3 /opt/hands-off-engine/scripts/coordination_agent.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/hands-off/coordination.log
StandardError=append:/var/log/hands-off/coordination-error.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable coordination-agent
sudo systemctl start coordination-agent

# Verify
sudo systemctl status coordination-agent

# Monitor
tail -f /var/log/hands-off/coordination.log
```

**Validation:**
- [ ] Service running
- [ ] Processes messages from `ai/coordination/messages.jsonl`
- [ ] Updates `ai/coordination/status.json`
- [ ] No errors in log

---

## Phase 2: Telegram Integration

### 2.1 Configure Credentials

**Steps:**

```bash
# Option A: Environment variables (recommended for services)
sudo tee -a /etc/environment > /dev/null << 'EOF'
TELEGRAM_BOT_TOKEN="8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA"
TELEGRAM_CHAT_ID="8327766663"
EOF

# Option B: .env file (for local testing)
cat > .env.telegram << 'EOF'
TELEGRAM_BOT_TOKEN=8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA
TELEGRAM_CHAT_ID=8327766663
EOF

# Reload environment
source /etc/environment

# Verify
echo $TELEGRAM_BOT_TOKEN
# Should show token
```

### 2.2 Test Telegram Bot

**Steps:**

```bash
# Install dependencies
pip3 install python-telegram-bot requests

# Test bot locally
python3 scripts/telegram_command_bot.py --test

# Expected: Connects to Telegram, shows available commands
# Send test notification
python3 -c "
import requests
import os

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')
message = '🧪 Test notification from Hands-Off Engine'

url = f'https://api.telegram.org/bot{token}/sendMessage'
r = requests.post(url, json={'chat_id': chat_id, 'text': message})
print('Response:', r.json())
"

# Check Telegram app - should receive message
```

**Validation:**
- [ ] Test message received in Telegram
- [ ] No errors in bot test
- [ ] Commands list shows properly

### 2.3 Deploy Telegram Bot Service

**Steps:**

```bash
# Create service
sudo tee /etc/systemd/system/hands-off-telegram.service > /dev/null << 'EOF'
[Unit]
Description=Hands-Off Engine Telegram Command Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/hands-off-engine
Environment="TELEGRAM_BOT_TOKEN=8214203655:AAGkAamvjQq0b7T7lmaTPDd-yYY_hvo_xvA"
Environment="TELEGRAM_CHAT_ID=8327766663"
ExecStart=/usr/bin/python3 /opt/hands-off-engine/scripts/telegram_command_bot.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/hands-off/telegram.log
StandardError=append:/var/log/hands-off/telegram-error.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable hands-off-telegram
sudo systemctl start hands-off-telegram

# Verify
sudo systemctl status hands-off-telegram
```

### 2.4 Test Telegram Commands

**Send these commands in Telegram and verify responses:**

| Command | Expected Response |
|---------|------------------|
| `/status` | System status summary |
| `/health` | Health check results |
| `/metrics` | Performance metrics |
| `/agents` | AI coordination status |
| `/help` | Command list |

**Validation:**
- [ ] All commands respond
- [ ] Responses are accurate
- [ ] No timeout errors
- [ ] Bot shows online in Telegram

---

## Phase 3: Cron Automation

### 3.1 Install Cron Jobs

**Steps:**

```bash
# Run auto-setup script
python3 scripts/auto_setup_cron.py --status

# Should show: No HANDS-OFF cron jobs found

# Install all jobs
python3 scripts/auto_setup_cron.py --install

# Verify installation
crontab -l | grep HANDS-OFF

# Expected output:
# HANDS-OFF: trading_pipeline - 0 * * * *
# HANDS-OFF: social_promotion - 0 */4 * * *
# HANDS-OFF: health_check - */15 * * * *
# HANDS-OFF: daily_recalibration - 0 8 * * *
# HANDS-OFF: performance_report - 0 20 * * *
# HANDS-OFF: coordination_agent - */5 * * * *
# HANDS-OFF: phase_progression - 0 0 * * *
```

**Validation:**
- [ ] 7 cron jobs installed
- [ ] All marked with HANDS-OFF
- [ ] Schedules match documentation

### 3.2 Test Cron Jobs

**Test each job manually:**

```bash
# 1. Trading pipeline
python3 ho_autoloop.py
# Should run without errors

# 2. Social promotion (if credentials set)
python3 api/social_promotion.py
# Should post or queue

# 3. Health check
./scripts/healthcheck.sh
# Should report system health

# 4. Phase progression
python3 scripts/autonomous_phase_manager.py
# Should evaluate trading phase

# 5. Performance report
# (If implemented)
```

**Validation:**
- [ ] Each script runs without errors
- [ ] Logs created in expected locations
- [ ] State files updated appropriately

### 3.3 Monitor Cron Execution

**Wait 24 hours, then check:**

```bash
# Check cron logs
grep HANDS-OFF /var/log/syslog | tail -20

# Check application logs
ls -lth /var/log/hands-off/ | head -10

# Verify jobs ran
cat logs/pipeline_*.log | grep -i "complete\|success" | tail -5
```

**Validation:**
- [ ] All jobs executed on schedule
- [ ] No error messages in logs
- [ ] State files updated correctly

---

## Phase 4: Verification & Testing

### 4.1 End-to-End Test

**Scenario:** Complete autonomous cycle

```bash
# 1. Simulate issue for self-healing
touch .git/index.lock
# Wait 5 minutes
# Check: Lock should be auto-removed
ls .git/index.lock  # Should not exist

# 2. Send AI coordination message
cat >> ai/coordination/messages.jsonl << 'EOF'
{"timestamp": "2025-12-01T20:00:00Z", "from": "test", "to": "copilot", "message": "Test coordination", "task_id": "test-001"}
EOF
# Wait 5 minutes
# Check: Message should be processed (check logs)

# 3. Test Telegram control
# Send /status via Telegram
# Verify response received

# 4. Wait for hourly pipeline
# Check logs for successful execution
```

**Validation:**
- [ ] Self-healing detected and fixed issue
- [ ] Coordination agent processed message
- [ ] Telegram responded to command
- [ ] Pipeline executed on schedule

### 4.2 Stress Test

**Create multiple issues simultaneously:**

```bash
# Stale lock
touch .git/index.lock

# Stale data
touch -t 202501010000 state/polymarket_positions.json

# Send multiple coordination messages
for i in {1..5}; do
  echo "{\"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"from\": \"test\", \"to\": \"copilot\", \"message\": \"Stress test $i\", \"task_id\": \"stress-$i\"}" >> ai/coordination/messages.jsonl
done

# Send Telegram commands rapidly
# (Send /status, /health, /metrics in quick succession)

# Wait 10 minutes
# Verify all issues resolved, all messages processed, all commands responded
```

**Validation:**
- [ ] All issues auto-fixed
- [ ] All messages processed
- [ ] All commands responded
- [ ] No service crashes
- [ ] Logs show graceful handling

---

## Phase 5: Post-Activation

### 5.1 Update Documentation

**Update these files to reflect activation:**

```bash
# Update deployment status
cat > ai/DEPLOYMENT_STATUS.md << 'EOF'
# Autonomous Architecture - Deployment Status

**Last Updated:** $(date -u +%Y-%m-%d)
**Status:** ✅ FULLY OPERATIONAL

## Deployed Services

| Service | Status | PID | Uptime |
|---------|--------|-----|--------|
| Self-Healing Agent | ✅ Running | $(pgrep -f self_healing_agent) | $(systemctl show -p ActiveEnterTimestamp self-healing-agent) |
| Coordination Agent | ✅ Running | $(pgrep -f coordination_agent) | $(systemctl show -p ActiveEnterTimestamp coordination-agent) |
| Telegram Bot | ✅ Running | $(pgrep -f telegram_command_bot) | $(systemctl show -p ActiveEnterTimestamp hands-off-telegram) |

## Cron Jobs

$(crontab -l | grep HANDS-OFF | wc -l) jobs active

## Verification

Last self-healing check: $(cat state/self_healing_state.json | jq -r .last_check)
Last coordination update: $(cat ai/coordination/status.json | jq -r .last_updated)

System is fully autonomous.
EOF
```

**Validation:**
- [ ] All documentation updated
- [ ] Status reflects reality
- [ ] Timestamps accurate

### 5.2 Update Coordination Status

```bash
# Update status.json
python3 << 'EOF'
import json
from datetime import datetime

with open('ai/coordination/status.json', 'r') as f:
    status = json.load(f)

status['last_updated'] = datetime.utcnow().isoformat() + 'Z'
status['active_system_status'] = 'FULLY AUTONOMOUS + OPERATIONAL'
status['autonomous_mode']['activated'] = datetime.utcnow().isoformat() + 'Z'

# Add activation record
if 'pending_tasks' in status:
    for task in status['pending_tasks']:
        if task['id'] == 'zero-touch-architecture':
            task['status'] = 'completed'
            task['completed_at'] = datetime.utcnow().isoformat() + 'Z'
            task['notes'] = 'All services deployed and running'

with open('ai/coordination/status.json', 'w') as f:
    json.dump(status, f, indent=2)

print("✓ Coordination status updated")
EOF
```

### 5.3 Send Completion Notification

```bash
# Notify via Telegram
python3 << 'EOF'
import requests
import os
from datetime import datetime

token = os.getenv('TELEGRAM_BOT_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

message = f"""🚀 <b>AUTONOMOUS ACTIVATION COMPLETE</b>

All documented autonomous features are now active:

✅ Self-Healing Agent (24/7)
✅ Coordination Agent (24/7)
✅ Telegram Command Bot (24/7)
✅ Auto-Merge Workflow (GitHub)
✅ Cron Jobs ({$(crontab -l | grep HANDS-OFF | wc -l)} tasks)

<b>System Status:</b> Fully Autonomous
<b>Primary Interface:</b> Telegram
<b>CLI Usage:</b> Emergency Only

<b>Available Commands:</b>
/status - System summary
/health - Health check
/metrics - Performance data
/agents - AI coordination
/help - All commands

<i>Activated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}</i>

The system now operates autonomously as documented.
"""

url = f'https://api.telegram.org/bot{token}/sendMessage'
r = requests.post(url, json={'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'})
print('Notification sent:', r.json().get('ok'))
EOF
```

---

## Phase 6: Monitoring & Validation

### 6.1 24-Hour Watch

**Monitor for first 24 hours:**

```bash
# Watch all service logs
tail -f /var/log/hands-off/*.log

# Check service status periodically
watch -n 60 'systemctl status self-healing-agent coordination-agent hands-off-telegram | grep Active'

# Monitor cron execution
watch -n 300 'grep HANDS-OFF /var/log/syslog | tail -5'
```

**Create monitoring checklist:**

| Time | Self-Healing | Coordination | Telegram | Cron | Issues |
|------|--------------|--------------|----------|------|--------|
| Hour 0 | ✅ | ✅ | ✅ | - | None |
| Hour 1 | ✅ | ✅ | ✅ | ✅ | None |
| Hour 4 | ✅ | ✅ | ✅ | ✅ | None |
| Hour 8 | ✅ | ✅ | ✅ | ✅ | None |
| Hour 24 | ✅ | ✅ | ✅ | ✅ | None |

### 6.2 Success Metrics

**After 24 hours, verify:**

```bash
# 1. No service crashes
systemctl show self-healing-agent | grep ActiveState=active
systemctl show coordination-agent | grep ActiveState=active
systemctl show hands-off-telegram | grep ActiveState=active

# 2. All cron jobs executed
grep HANDS-OFF /var/log/syslog | grep -c "$(date +%Y-%m-%d)"
# Should be ≥ 50 (various jobs throughout day)

# 3. Auto-healing working
cat state/self_healing_state.json | jq '.total_fixes'
# Should be > 0 if any issues detected

# 4. Telegram responsive
# Send /status and verify response time < 5 seconds

# 5. No errors
grep -i error /var/log/hands-off/*.log | wc -l
# Should be 0 or minimal
```

**Target Metrics:**
- [ ] 100% service uptime
- [ ] All cron jobs executed
- [ ] Telegram response time < 5s
- [ ] Zero critical errors
- [ ] Auto-healing events logged

---

## Rollback Procedure

If issues occur:

```bash
# Stop all services
sudo systemctl stop self-healing-agent
sudo systemctl stop coordination-agent
sudo systemctl stop hands-off-telegram

# Disable services
sudo systemctl disable self-healing-agent
sudo systemctl disable coordination-agent
sudo systemctl disable hands-off-telegram

# Remove cron jobs
python3 scripts/auto_setup_cron.py --remove

# Verify cleanup
systemctl list-units | grep hands-off  # Should be empty
crontab -l | grep HANDS-OFF  # Should be empty

# System reverts to manual CLI operation
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check service file syntax
systemd-analyze verify /etc/systemd/system/self-healing-agent.service

# Check for port conflicts
sudo lsof -i :8000  # If service uses ports

# Check permissions
ls -l /opt/hands-off-engine/scripts/*.py

# Check logs
journalctl -u self-healing-agent -n 50
```

### Telegram Not Responding

```bash
# Test token
curl "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/getMe"

# Test connectivity
nc -zv api.telegram.org 443

# Check bot logs
tail -100 /var/log/hands-off/telegram.log
```

### Cron Jobs Not Running

```bash
# Check cron daemon
sudo systemctl status cron

# Check user crontab
crontab -l

# Test manual execution
/usr/bin/python3 /opt/hands-off-engine/ho_autoloop.py

# Check cron logs
grep CRON /var/log/syslog | tail -20
```

---

## Summary

**Pre-Activation:**
- Code exists, services not running
- Manual CLI operation
- 0% autonomous

**Post-Activation:**
- All services running 24/7
- Telegram primary interface
- 99% autonomous

**Timeline:** 1-2 hours for core activation, 24h for validation

**Risk:** Low (code tested, rollback available)

**Next:** Monitor for 48h, then consider fully autonomous

---

**Runbook Version:** 1.0  
**Last Updated:** 2025-12-01  
**Status:** Ready for execution
