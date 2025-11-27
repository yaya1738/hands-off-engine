# System Diagnostic Report - 2025-11-27

## Executive Summary

**The system is NOT generating autonomous cash.** Here's why:

### 🔴 Critical Blockers (In Order of Importance)

| Blocker | Impact | Fix Required |
|---------|--------|--------------|
| 1. Data Pipeline Stopped | No new market data since Nov 16 | Restart Termux fetchers |
| 2. Executor in Shadow Mode | All trades are simulated only | Set HANDS_OFF_EXECUTOR_MODE=live |
| 3. Live Trading Disabled | LIVE_TRADING_ENABLED env not set | Set LIVE_TRADING_ENABLED=1 |
| 4. No Automation Running | Pipeline doesn't auto-execute | Set up cron or scheduled workflow |

### 🟡 What's Working
- Trading infrastructure code: ✅ Complete
- Safety guardrails: ✅ Configured
- Shadow trade logging: ✅ Active
- Risk profile: ✅ Set (baby_mode, $50 max position)
- Coordination system: ✅ Active

---

## Blocker Details

### 1. 🔴 Data Pipeline Stopped

**Evidence:**
- Latest `polymarket-compact.json` timestamp: `2025-11-16T12:05:00Z` (11 days ago)
- No new `fetch-*.json` files after 2025-11-16
- Markets like "Ethereum above $X on November 16" have already resolved

**Root Cause:**
Termux node data fetchers have stopped running.

**Fix:**
On the Termux device:
```bash
cd ~/hands-off
./start_all.sh    # Restart all services
./status.sh       # Verify running
```

Or on the droplet if it's the syncing node:
```bash
ssh termux-phone  # If configured
./start_all.sh
```

---

### 2. 🔴 Executor in Shadow Mode

**Evidence:**
- Shadow trades logged in `state/shadow_trades.jsonl` show `executor_mode: "shadow"`
- Even with `live_trading_active: true`, trades are not executing

**Root Cause:**
`HANDS_OFF_EXECUTOR_MODE` environment variable defaults to `dryrun` if not set.
The executor mode check in `ho_executor_plan.py:32-54` returns "dryrun" by default.

**Current Behavior:**
```
Shadow trades → Logged to state/shadow_trades.jsonl
Real trades → NOT sent to Polymarket API
```

**Fix:**
Before running the pipeline:
```bash
export HANDS_OFF_EXECUTOR_MODE=live
```

Or add to systemd service / cron:
```bash
HANDS_OFF_EXECUTOR_MODE=live ./scripts/run_and_notify.sh
```

---

### 3. 🔴 Live Trading Not Enabled

**Evidence:**
- `executor/ho_executor_plan.py` line 29: `_ENV_LIVE_TRADING = os.getenv("LIVE_TRADING_ENABLED", "0") == "1"`
- Without this, `is_live_trading_enabled()` returns False immediately
- `state/trading_mode.json` shows `live_trading_enabled: true` BUT this is only checked AFTER the env var check

**Root Cause:**
The executor requires BOTH:
1. Environment variable: `LIVE_TRADING_ENABLED=1`
2. State file: `state/trading_mode.json` with `live_trading_enabled: true`

State file is correct, but environment variable is not set.

**Fix:**
```bash
export LIVE_TRADING_ENABLED=1
export HANDS_OFF_EXECUTOR_MODE=live
```

---

### 4. 🔴 No Automation Running

**Evidence:**
- No GitHub Action for scheduled trading
- No evidence of cron running on droplet
- Pipeline runs manually only

**Root Cause:**
The `SHADOW_MODE_RUNBOOK.md` documents how to set up cron, but it was never implemented for live trading.

**Fix:**
Add to droplet crontab:
```cron
# Live trading - every 4 hours (source credentials from .env.polymarket)
0 */4 * * * cd /root/hands-off-engine && source .env.polymarket && ./scripts/run_and_notify.sh >> /var/log/live-trades.log 2>&1
```

---

## Complete Fix Sequence

### Step 1: Restore Data Pipeline (Termux)
```bash
# On Termux device
cd ~/hands-off
./start_all.sh
./status.sh
# Verify: fetch-*.json files appearing in out/
```

### Step 2: Set Up Live Environment (Droplet)
```bash
# Create .env.polymarket with credentials (DO NOT commit to git!)
# Get your private key from your Polymarket wallet
vim /root/hands-off-engine/.env.polymarket

# Required variables:
# POLYMARKET_PRIVATE_KEY=<your-private-key>
# POLYMARKET_FUNDER_ADDRESS=<your-wallet-address>
# LIVE_TRADING_ENABLED=1
# HANDS_OFF_EXECUTOR_MODE=live

# Verify .env.polymarket is in .gitignore
grep -q ".env.polymarket" /root/hands-off-engine/.gitignore || echo ".env.polymarket" >> /root/hands-off-engine/.gitignore
```

### Step 3: Test Manual Run
```bash
cd /root/hands-off-engine
source .env.polymarket
./scripts/run_and_notify.sh --bankroll 241
# Check output and Polymarket for actual trade
```

### Step 4: Set Up Automation
```bash
# Add to crontab -e
0 */4 * * * cd /root/hands-off-engine && source .env.polymarket && ./scripts/run_and_notify.sh >> /var/log/trading.log 2>&1
```

---

## Risk Controls (Already in Place)

These safety measures are correctly configured:

| Control | Setting | Location |
|---------|---------|----------|
| Max position | $50 | config/hard_limits.json |
| Max daily loss | $200 | config/hard_limits.json |
| Min confidence | 40% | config/hard_limits.json |
| Risk phase | baby_mode | state/risk_profile.json |
| Auto-pause | Enabled | executor/trading_safeguards.py |

---

## Financial Context

From `finance/yair_finance_hub.json`:
- Polymarket balance: $241.36 USDC
- Deployable to trading: $241
- Monthly burn: $3,280
- Runway: < 1 month

**Critical insight:** AI costs (~$250/month) need to generate ROI. The system should be live and making autonomous trades.

---

## Next Agent Actions

For Claude-Code, Copilot, or other agents:

1. **Immediate**: Check Termux data pipeline status and restart if needed
2. **Short-term**: Create GitHub Action for scheduled trading execution
3. **Verify**: Confirm Polymarket API credentials are configured
4. **Monitor**: First live trade execution and Telegram notification

---

*Generated by Copilot investigation on 2025-11-27*
