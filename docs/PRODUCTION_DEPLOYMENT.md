# Production Deployment Guide

**Last Updated:** 2025-11-21
**Status:** Production-ready (DRYRUN mode)

---

## Overview

This guide covers deploying the Hands-Off Engine for automated trading signal generation and notification.

**Complete Pipeline:**
```
Polymarket Data → Alpha Sync → Decider → Executor → Notifications → Your Phone
    (external)    (automated)   (AI)    (safety)   (Telegram)      (review)
```

---

## Prerequisites

### Required

1. **Python 3.8+** with packages:
   ```bash
   pip install requests openai
   ```

2. **Polymarket data source** (termux-hands-off/out/polymarket-compact.json)
   - Must be refreshed regularly (separate process)

3. **Telegram bot** (for notifications):
   - Bot token from @BotFather
   - Your chat ID
   - Stored in `~/hands-off/state/tg/bots/handsoff.env`:
     ```
     TOKEN=your_bot_token
     CHAT_ID=your_chat_id
     ```

### Optional

4. **IFTTT webhook** (backup notifications):
   - Webhook key from ifttt.com/maker_webhooks
   - Stored in `~/hands-off/ifttt.env`:
     ```
     IFTTT_WEBHOOK_KEY=your_key
     IFTTT_EVENT_NAME=execution_plan
     ```

5. **OpenAI API key** (if using AI-enhanced planning):
   - Set `OPENAI_API_KEY` environment variable

---

## Quick Start

### 1. Test Pipeline Manually

```bash
cd /root/hands-off-engine

# Run full pipeline with notifications
./scripts/run_and_notify.sh

# Check output
cat executor/execution_plan.json
```

**Expected output:**
- ✓ Alpha signals synced
- ✓ Actions planned
- ✓ Safety checks passed (some actions)
- ✓ Notification sent to Telegram

### 2. Verify Notification Received

Check your Telegram for message like:
```
🔵 DRYRUN Execution Plan

📊 Summary: 2 orders, $56 total
⏰ 2025-11-21T09:39:22

Orders:
1. [market] Will Bitcoin dip to $80,000 in November?
   yes • $28
...
```

---

## Automated Execution (Cron)

### Setup Cron Job

```bash
crontab -e
```

Add one of these schedules:

#### Every 15 minutes (high frequency)
```cron
*/15 * * * * cd /root/hands-off-engine && ./scripts/run_and_notify.sh >> /var/log/hands-off-engine.log 2>&1
```

#### Every hour
```cron
0 * * * * cd /root/hands-off-engine && ./scripts/run_and_notify.sh >> /var/log/hands-off-engine.log 2>&1
```

#### Twice daily (morning and evening)
```cron
0 9,21 * * * cd /root/hands-off-engine && ./scripts/run_and_notify.sh >> /var/log/hands-off-engine.log 2>&1
```

#### Market hours only (9 AM - 9 PM EST, Mon-Fri)
```cron
0 9-21 * * 1-5 cd /root/hands-off-engine && ./scripts/run_and_notify.sh >> /var/log/hands-off-engine.log 2>&1
```

### Create Log Directory

```bash
sudo touch /var/log/hands-off-engine.log
sudo chown $USER /var/log/hands-off-engine.log
```

### Test Cron Execution

```bash
# Run as cron would (no terminal, minimal env)
env -i /bin/bash -c "cd /root/hands-off-engine && ./scripts/run_and_notify.sh"
```

---

## Monitoring

### Check Last Run

```bash
# View recent log entries
tail -50 /var/log/hands-off-engine.log

# Check execution plan timestamp
cat executor/execution_plan.json | grep timestamp
```

### Monitor Script (Continuous)

```bash
# Create monitoring script
cat > scripts/monitor.sh << 'EOF'
#!/bin/bash
while true; do
    clear
    echo "=== Hands-Off Engine Status ==="
    echo "Time: $(date)"
    echo
    echo "Last execution plan:"
    if [ -f executor/execution_plan.json ]; then
        python3 -c "import json; d=json.load(open('executor/execution_plan.json')); print(f\"  Generated: {d['timestamp']}\"); print(f\"  Orders: {d['total_orders']}\"); print(f\"  Total: \${d['total_size_usd']}\")"
    else
        echo "  No plan generated yet"
    fi
    echo
    echo "Last 5 log entries:"
    tail -5 /var/log/hands-off-engine.log 2>/dev/null || echo "  No logs yet"
    sleep 10
done
EOF

chmod +x scripts/monitor.sh
./scripts/monitor.sh
```

### Health Check Endpoint (Optional)

```bash
# Create simple health check
cat > scripts/healthcheck.py << 'EOF'
#!/usr/bin/env python3
import json
from datetime import datetime, timedelta
from pathlib import Path

plan_file = Path('executor/execution_plan.json')
if not plan_file.exists():
    print("WARN: No execution plan exists")
    exit(1)

with open(plan_file) as f:
    plan = json.load(f)

timestamp = datetime.fromisoformat(plan['timestamp'].replace('Z', '+00:00'))
age = datetime.now().astimezone() - timestamp

if age > timedelta(hours=2):
    print(f"WARN: Execution plan is {age.total_seconds()/3600:.1f} hours old")
    exit(1)

print(f"OK: Plan generated {age.total_seconds()/60:.0f} minutes ago")
exit(0)
EOF

chmod +x scripts/healthcheck.py
```

---

## Safety Checks

### Current Safety Parameters

**In Executor (`executor/ho_executor_plan.py`):**
- `MAX_POSITION_SIZE = 100.0` - Max $100 per position
- `MIN_CONFIDENCE_THRESHOLD = 0.7` - Minimum 70% confidence required
- Default mode: `DRYRUN = True` - No real trades

**In Decider (`decider/ho_decider.py`):**
- Kelly criterion sizing (conservative)
- Confidence-based position scaling
- Bankroll-aware allocation

### Changing to LIVE Mode

⚠️ **WARNING: This enables real money trading!**

```bash
# Edit run_pipeline.py to set dryrun=False
# OR pass --live flag:
./scripts/run_and_notify.sh --live

# Strongly recommended: Start with small bankroll
./scripts/run_and_notify.sh --live --bankroll 100
```

**Before going live:**
1. ✅ Test DRYRUN for at least 1 week
2. ✅ Verify notifications are reliable
3. ✅ Review safety parameters
4. ✅ Start with minimal bankroll ($50-100)
5. ✅ Monitor first 24 hours closely
6. ✅ Implement actual trading API (currently placeholder)

---

## Troubleshooting

### Pipeline Not Running

**Check cron is active:**
```bash
sudo service cron status
# Should show "active (running)"
```

**Check cron logs:**
```bash
grep CRON /var/log/syslog | tail -20
```

**Test manually:**
```bash
cd /root/hands-off-engine
./scripts/run_and_notify.sh
```

### No Notifications Received

**Check env files exist:**
```bash
cat ~/hands-off/state/tg/bots/handsoff.env
# Should show TOKEN and CHAT_ID
```

**Test notification script directly:**
```bash
echo "Test message" | python3 termux-hands-off/agent/notify.py
```

**Check Telegram bot is active:**
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

### No Actions Passing Safety Checks

**This is normal and expected!**

Safety checks are intentionally strict:
- Most market opportunities don't meet the 70% confidence threshold
- Position sizing limits prevent oversized bets
- This is working as designed

**If you consistently get 0 actions:**
1. Check alpha signals have reasonable edges (>3%)
2. Verify confidence calculations are working
3. Consider lowering `MIN_CONFIDENCE_THRESHOLD` (carefully!)
4. Review market selection criteria

### Pipeline Errors

**Check full error log:**
```bash
tail -100 /var/log/hands-off-engine.log
```

**Common issues:**
- Missing input data (polymarket-compact.json not updated)
- Invalid JSON in data files
- Missing environment variables
- Network issues (API calls timeout)

**Debug mode:**
```bash
python3 scripts/run_pipeline.py --verbose
```

---

## Performance Tuning

### Adjust Frequency

**High frequency** (every 15 min):
- ✅ Catch opportunities quickly
- ✅ React to market changes fast
- ❌ More compute/API usage
- ❌ More notifications (can be noisy)

**Low frequency** (twice daily):
- ✅ Fewer notifications
- ✅ Less resource usage
- ❌ Might miss time-sensitive opportunities
- ❌ Slower to react

**Recommended:** Start with hourly, adjust based on results.

### Notification Filtering

**Only notify if >N orders:**
```bash
# Edit run_and_notify.sh to add:
ORDERS=$(jq '.total_orders' executor/execution_plan.json)
if [ "$ORDERS" -lt 3 ]; then
    echo "Only $ORDERS orders, skipping notification"
    exit 0
fi
```

**Only notify if >$X total:**
```bash
TOTAL=$(jq '.total_size_usd' executor/execution_plan.json)
if (( $(echo "$TOTAL < 50" | bc -l) )); then
    echo "Only \$$TOTAL, skipping notification"
    exit 0
fi
```

---

## Backup & Recovery

### Backup Critical Files

```bash
# Create backup script
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR=~/hands-off-backups/$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

cp executor/execution_plan.json $BACKUP_DIR/ 2>/dev/null
cp state/polymarket-model.json $BACKUP_DIR/ 2>/dev/null
cp /var/log/hands-off-engine.log $BACKUP_DIR/ 2>/dev/null

echo "Backup saved to $BACKUP_DIR"
EOF

chmod +x scripts/backup.sh

# Run daily backup via cron
# 0 0 * * * /root/hands-off-engine/scripts/backup.sh
```

### Restore from Backup

```bash
# List backups
ls -lh ~/hands-off-backups/

# Restore specific backup
cp ~/hands-off-backups/20251121_093000/* /root/hands-off-engine/executor/
```

---

## Upgrade Path

### To LIVE Mode

1. Test DRYRUN for 1-2 weeks
2. Implement actual trading API in `executor/ho_executor_plan.py`
3. Start with minimal bankroll
4. Monitor closely for 48 hours
5. Gradually increase bankroll

### Future Enhancements

**Planned:**
- Real alpha model (replace placeholder fair price estimation)
- Actual Polymarket liquidity queries
- Backtesting framework
- Performance dashboard
- Multi-exchange support
- Advanced position sizing (Kelly+)
- Machine learning model integration

---

## Production Checklist

Before running in production:

- [ ] Tested pipeline manually (DRYRUN)
- [ ] Notifications received successfully
- [ ] Cron job configured
- [ ] Log rotation set up
- [ ] Monitoring script running
- [ ] Backups configured
- [ ] Safety parameters reviewed
- [ ] Emergency stop procedure documented
- [ ] DRYRUN tested for 1+ week
- [ ] Ready for LIVE (if applicable)

---

## Emergency Stop

If something goes wrong:

```bash
# Stop cron jobs
crontab -e
# Comment out hands-off-engine lines

# Or disable cron entirely
sudo service cron stop

# Check no processes running
ps aux | grep hands-off

# Review what happened
tail -200 /var/log/hands-off-engine.log
```

---

## Support

**Documentation:**
- `alpha/README.md` - Alpha signals pipeline
- `docs/EXECUTION_NOTIFICATIONS.md` - Notification setup
- `.claude/AI_AGENT_COORDINATION_LOG.md` - Development history

**Issues:**
- Check logs first
- Run manual test with --verbose
- Review safety parameters

---

**Deployed by:** Claude Code (autonomous)
**Date:** 2025-11-21
**Status:** Production-ready (DRYRUN mode)
