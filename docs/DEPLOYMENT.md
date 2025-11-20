# Deployment Guide - Trading Pipeline Updates

## What Was Updated (2025-11-20)

### New Files
1. **pm_enrich_model.py** - Enriches model with live prices and computed edges
2. **pm_decide.py** - Generates DRYRUN orders based on edge thresholds
3. **hoenrich.sh** - Shell wrapper for enrichment script
4. **hodecide.sh** - Shell wrapper for decider script
5. **TRADING_PIPELINE.md** - Complete documentation of the pipeline

### Modified Files
1. **hogitpull** - Updated to auto-detect droplet repo path

## Deployment Steps

### 1. Pull Latest Changes to Droplet

From Termux or your local environment:

```bash
# Navigate to the agent scripts directory
cd ~/hands-off-engine/termux-hands-off/bin

# Pull latest code to droplet
./hogitpull
```

This will:
- Detect whether droplet uses `/root/hands-off` or `/root/hands-off-engine`
- Pull latest changes from GitHub
- Make new scripts available on the droplet

### 2. Verify Deployment

Check that the new scripts are present:

```bash
ssh do138 'ls -la /root/hands-off*/termux-hands-off/agent/pm_*.py'
```

Expected output:
```
-rwxr-xr-x 1 root root  xxxx Nov 20 xx:xx pm_decide.py
-rwxr-xr-x 1 root root  xxxx Nov 20 xx:xx pm_enrich_model.py
```

### 3. Test the Pipeline

From Termux, navigate to the agent scripts:

```bash
cd ~/hands-off-engine/termux-hands-off/agent

# Test enrichment
./hoenrich.sh

# Test decider
./hodecide.sh

# View generated orders
./hoorders.sh

# Get full snapshot
./hosnapshot.sh
```

## Nexus Sync (if applicable)

If you have a Nexus environment that needs syncing:

```bash
# Check if there's a nexus sync script
ls -la ~/hands-off*/termux/nexus*.sh

# Or use git pull on nexus directly
ssh nexus 'cd /path/to/hands-off-engine && git pull origin main'
```

## Rollback Procedure

If something goes wrong:

```bash
# On droplet
ssh do138 'cd /root/hands-off-engine && git log --oneline -5'

# Revert to previous commit
ssh do138 'cd /root/hands-off-engine && git reset --hard <previous-commit-hash>'
```

## Troubleshooting

### "No such file or directory" errors

**Symptom**: Scripts can't find Python files on droplet

**Solution**: Check repo path
```bash
ssh do138 'ls -la /root/ | grep hands-off'
```

If repo is at different path, update these variables in the scripts:
- `hoenrich.sh`: Line 8
- `hodecide.sh`: Line 8

### Python import errors

**Symptom**: ModuleNotFoundError or ImportError

**Solution**: Verify Python environment on droplet
```bash
ssh do138 'python3 --version'
ssh do138 'which python3'
```

### Permission denied errors

**Solution**: Make scripts executable
```bash
ssh do138 'chmod +x /root/hands-off*/termux-hands-off/agent/*.py'
ssh do138 'chmod +x /root/hands-off*/termux-hands-off/agent/*.sh'
```

### Path mismatch errors

If scripts reference wrong paths:

1. Check actual repo location on droplet:
   ```bash
   ssh do138 'pwd && git remote -v'
   ```

2. Update hogitpull if needed to match actual path

## Configuration After Deployment

### Set Fair Values

The model needs your probability estimates (fair_yes values). Edit on droplet:

```bash
ssh do138
nano /root/hands-off-out/state/polymarket-model.json
```

Example:
```json
{
  "events": [
    {
      "id": "btc-100k",
      "side": "YES",
      "fair_yes": 0.65,  // ← Set your probability estimate here
      "alloc": {
        "max_usd": 4.29
      }
    }
  ]
}
```

### Adjust Global Settings

Edit globals in polymarket-model.json:

```json
{
  "globals": {
    "budget_usd": 30.0,               // Total budget
    "default_stake_usd": 5.0,          // Default position size
    "min_edge_to_bet_pct_points": 3.0  // Min edge (3pp = 3%)
  }
}
```

## Integration with Existing Cron/Systemd

If you want to run enrichment + decider automatically:

### Option 1: Add to existing cron

```bash
# On Termux
crontab -e

# Add these lines (example: run every 5 minutes)
*/5 * * * * ~/hands-off-engine/termux-hands-off/agent/hoenrich.sh >> ~/logs/enrich.log 2>&1
*/5 * * * * ~/hands-off-engine/termux-hands-off/agent/hodecide.sh >> ~/logs/decide.log 2>&1
```

### Option 2: Add to droplet systemd timer

Create `/etc/systemd/system/ho-pipeline.service`:

```ini
[Unit]
Description=Hands-Off Trading Pipeline
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /root/hands-off/termux-hands-off/agent/pm_enrich_model.py
ExecStart=/usr/bin/python3 /root/hands-off/termux-hands-off/agent/pm_decide.py
User=root

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/ho-pipeline.timer`:

```ini
[Unit]
Description=Run Hands-Off Pipeline every 5 minutes

[Timer]
OnBootSec=1min
OnUnitActiveSec=5min

[Install]
WantedBy=timers.target
```

Enable:
```bash
systemctl enable ho-pipeline.timer
systemctl start ho-pipeline.timer
```

## Monitoring

### Check Pipeline Health

```bash
# View enrichment output
ssh do138 'tail -50 /root/hands-off-out/state/polymarket-model.json'

# View decisions
ssh do138 'tail -50 /root/hands-off-out/state/decision_report.json'

# Check timestamps
./hosnapshot.sh | grep as_of
```

### View Logs

```bash
# If using cron
tail -f ~/logs/enrich.log
tail -f ~/logs/decide.log

# If using systemd
ssh do138 'journalctl -u ho-pipeline -f'
```

## Safety Reminders

⚠️ **Current Mode: DRYRUN ONLY**

- No actual trades are being executed
- decision_report.json contains plans, not executed orders
- Review DRYRUN output carefully before enabling LIVE mode
- Start with small position sizes when going live

## Support

For issues or questions:
- Check [TRADING_PIPELINE.md](./TRADING_PIPELINE.md) for detailed pipeline docs
- Review logs for error messages
- Verify all file paths match your actual deployment

## Branch Information

**Active Branch**: `claude/engine-snapshot-budget-014TEzB7fsTQE1bv6kSgKm4V`

**Commits**:
1. `499a731` - feat: add model enrichment and decider for edge-based DRYRUN orders
2. `a05f8b1` - fix: update droplet paths to support both hands-off and hands-off-engine

**PR Link**: https://github.com/yaya1738/hands-off-engine/pull/new/claude/engine-snapshot-budget-014TEzB7fsTQE1bv6kSgKm4V
