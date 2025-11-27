# Shadow Mode Operator Runbook

**Purpose:** Run the trading system in shadow mode to validate safety layers and observe performance without risk.

---

## Operator TL;DR (Shadow Mode)

**Goal:** Run the full pipeline with zero real trades, logging all would-be orders to `state/shadow_trades.jsonl`.

### 1. One-time sanity check

- Confirm hard limits: `config/hard_limits.json` (e.g. $200 max position, $400 daily loss, etc.).
- Confirm risk profile: `state/risk_profile.json` is in baby mode ($50 positions / conservative).
- Ensure executor mode is NOT `live`:
  - `HANDS_OFF_EXECUTOR_MODE` should be `shadow` or unset.

> Note: If your runtime directory is `/root/hands-off-out` (mirror v4), use that instead of `/root/hands-off-engine` in the commands below.

### 2. Manual single run (droplet SSH session, as root)

```bash
# On DROPLET ROOT SHELL (Termux → ssh root@<droplet>)
cd /root/hands-off-engine    # or /root/hands-off-out if that's your runtime
export HANDS_OFF_EXECUTOR_MODE=shadow
./scripts/run_and_notify.sh --bankroll 5000
```

Check results:

```bash
# Still on DROPLET ROOT SHELL
tail -n 50 state/shadow_trades.jsonl
```

You should see JSON lines with market, side, size, confidence, phase, safeguards, etc.

### 3. Enable hourly automation (cron)

```cron
# On DROPLET ROOT SHELL: crontab -e
0 * * * * cd /root/hands-off-engine && HANDS_OFF_EXECUTOR_MODE=shadow ./scripts/run_and_notify.sh >> /var/log/shadow-trades.log 2>&1
```

Let this run for 1–2 weeks before considering `live` mode.

### 4. Quick health check

* File exists and growing: `state/shadow_trades.jsonl`
* No crashes in logs: `/var/log/shadow-trades.log`
* Hard limits never exceeded when you inspect the file
* `extra.allowed_by_safeguards` correctly flips between true/false

---

## Quick Start

### Enable Shadow Mode

```bash
# Set executor mode
export HANDS_OFF_EXECUTOR_MODE=shadow

# Verify mode
python3 -c "
import os
os.environ['HANDS_OFF_EXECUTOR_MODE'] = 'shadow'
from executor.ho_executor_plan import get_executor_mode
print(f'Executor mode: {get_executor_mode()}')
"
# Should print: Executor mode: shadow
```

### Run One Cycle Manually

```bash
cd /root/hands-off-engine
export HANDS_OFF_EXECUTOR_MODE=shadow
./scripts/run_and_notify.sh --bankroll 5000
```

### Enable Hourly Automation

Add to crontab:
```bash
# Shadow mode trading (hourly)
0 * * * * cd /root/hands-off-engine && HANDS_OFF_EXECUTOR_MODE=shadow ./scripts/run_and_notify.sh >> /var/log/shadow-trades.log 2>&1
```

Or via systemd timer (recommended for better control).

---

## Monitoring

### View Shadow Trades Log

```bash
# Tail live
tail -f state/shadow_trades.jsonl

# View last 10 trades
tail -10 state/shadow_trades.jsonl | python3 -m json.tool
```

### Analyze Shadow Performance

```bash
python3 << 'EOF'
import json
from pathlib import Path

shadow_log = Path("state/shadow_trades.jsonl")

if not shadow_log.exists():
    print("No shadow trades yet")
    exit()

trades = [json.loads(line) for line in open(shadow_log)]

print(f"\n=== SHADOW TRADE ANALYSIS ===\n")
print(f"Total trades logged: {len(trades)}")

# Count by status
blocked_by_safeguards = [t for t in trades if not t.get("extra", {}).get("allowed_by_safeguards", True)]
passed_safeguards = [t for t in trades if t.get("extra", {}).get("allowed_by_safeguards", False)]

print(f"Blocked by safeguards: {len(blocked_by_safeguards)}")
print(f"Would have executed: {len(passed_safeguards)}")

# Health check stats
healthy_cycles = [t for t in trades if t.get("health_ok", False)]
unhealthy_cycles = [t for t in trades if not t.get("health_ok", False)]

print(f"\nHealth check passes: {len(healthy_cycles)}")
print(f"Health check failures: {len(unhealthy_cycles)}")

# Phase distribution
phases = {}
for t in trades:
    phase = t.get("risk_phase", "unknown")
    phases[phase] = phases.get(phase, 0) + 1

print(f"\nPhase distribution:")
for phase, count in phases.items():
    print(f"  {phase}: {count}")

# Total volume
total_volume = sum(t.get("size_usd", 0) for t in trades)
print(f"\nTotal shadow volume: ${total_volume:.2f}")

# Recent trades
print(f"\n=== LAST 5 TRADES ===")
for trade in trades[-5:]:
    print(f"{trade['timestamp'][:19]}: {trade['side']} ${trade['size_usd']:.0f} on {trade['market_name']}")
    print(f"  Health: {trade['health_reason']}, Phase: {trade['risk_phase']}")
    if trade.get("caps_applied"):
        print(f"  Caps applied: {', '.join(trade['caps_applied'])}")

EOF
```

---

## What to Look For

### Good Signs (Shadow Mode Working Correctly)
- ✅ Shadow trades appearing in `state/shadow_trades.jsonl`
- ✅ Health checks mostly passing (>95%)
- ✅ Safeguards occasionally blocking (shows they're working)
- ✅ Hard limits never exceeded (max_position ≤ $200)
- ✅ Reasonable trade frequency (not 0, not excessive)
- ✅ Phase staying in `baby_mode` initially

### Warning Signs
- ⚠️ No trades logged (pipeline may not be running)
- ⚠️ All trades blocked (config may be too conservative)
- ⚠️ Health checks failing frequently (system degraded)
- ⚠️ Position sizes exceeding $200 (hard limits not enforced - critical bug)

### Red Flags (Stop and Investigate)
- 🚨 Shadow log shows trades > $200 (hard limits broken)
- 🚨 Confidence scores below 40% being logged (should be blocked)
- 🚨 Health check always failing (pipeline broken)

---

## Transitioning to Live

### Pre-Requisites
- ✅ At least 50+ shadow trades logged
- ✅ Health checks passing consistently
- ✅ Hard limits respected in all shadow trades
- ✅ Safeguards triggering appropriately
- ✅ No position > $200 in shadow log
- ✅ Reasonable would-be performance (you decide the threshold)

### Steps

1. **Review shadow performance:**
   ```bash
   # Run analysis script above
   # Manually review last 50 trades for sanity
   tail -50 state/shadow_trades.jsonl | less
   ```

2. **Add Polymarket credentials:**
   ```bash
   # Edit .env.polymarket
   vim .env.polymarket

   # Set:
   # POLYMARKET_PRIVATE_KEY=0x...
   # POLYMARKET_FUNDER_ADDRESS=0x...
   ```

3. **Switch to live mode:**
   ```bash
   export HANDS_OFF_EXECUTOR_MODE=live
   ```

4. **Enable trading:**
   ```bash
   python3 scripts/resume_trading.py
   ```

5. **Run ONE manual cycle:**
   ```bash
   ./scripts/run_and_notify.sh --bankroll 500
   ```

6. **Verify on Polymarket:**
   - Check Polymarket.com for actual trade
   - Verify amount matches expected
   - Check `logs/trading_performance.jsonl`

7. **Monitor for 48 hours** before enabling hourly automation.

---

## Troubleshooting

### No shadow trades appearing

**Check:**
```bash
# Is shadow mode set?
python3 -c "from executor.ho_executor_plan import get_executor_mode; print(get_executor_mode())"

# Is pipeline running?
./scripts/run_and_notify.sh --bankroll 5000

# Any errors?
tail -50 /var/log/hands-off-engine.log
```

### All trades blocked

**Check safeguards:**
```bash
# Review last trade's safety checks
tail -1 state/shadow_trades.jsonl | python3 -m json.tool | grep -A5 safety_checks

# Check risk profile
cat state/risk_profile.json

# Check hard limits
cat config/hard_limits.json
```

### Health checks failing

**Check health status:**
```bash
python3 << 'EOF'
from executor.trading_safeguards import check_trading_health
healthy, issues = check_trading_health()
print(f"Healthy: {healthy}")
if not healthy:
    print(f"Issues: {issues}")
EOF
```

**Common fixes:**
- Stale risk profile: Run `python3 scripts/recalibrate_engine.py`
- No recent activity: Expected if first run
- High error rate: Check recent failures in logs

---

## Commands Reference

### Start/Stop Shadow Mode

```bash
# Start (one-time)
export HANDS_OFF_EXECUTOR_MODE=shadow
./scripts/run_and_notify.sh

# Stop (if running via cron)
crontab -l | grep -v "HANDS_OFF_EXECUTOR_MODE=shadow" | crontab -
```

### View Logs

```bash
# Shadow trades
tail -f state/shadow_trades.jsonl

# System logs
tail -f /var/log/hands-off-engine.log

# Recalibration logs
tail -f /var/log/recalibration.log
```

### Switch Modes

```bash
# To shadow
export HANDS_OFF_EXECUTOR_MODE=shadow

# To dryrun
export HANDS_OFF_EXECUTOR_MODE=dryrun

# To live
export HANDS_OFF_EXECUTOR_MODE=live
```

---

## Safety Reminder

**Shadow mode NEVER sends real trades.** It's structurally impossible for shadow mode to call the trading API, even if other flags are misconfigured. This is enforced at the code level.

However, **live mode DOES send real trades** when:
- `HANDS_OFF_EXECUTOR_MODE=live`, AND
- `is_live_trading_enabled()` returns True, AND
- All safety gates pass

Always test mode transitions carefully and monitor the first live cycle closely.
