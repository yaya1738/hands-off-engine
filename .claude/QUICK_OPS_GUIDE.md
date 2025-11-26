# Quick Operations Guide
**For:** Termux Device Operations
**Updated:** 2025-11-26

---

## 🚀 MOST COMMON OPERATIONS

### 1. Check System Status
```bash
python3 tools/trading_dashboard.py
```
**What it shows:**
- Execution plan age and status
- Current mode (DRYRUN/LIVE)
- Tradeable markets count
- Expected value
- Recommendations

---

### 2. Regenerate Execution Plan
```bash
ho-cycle.sh
```
**What it does:**
1. Fetches fresh Polymarket data
2. Runs alpha model
3. Runs decider (with new filtering!)
4. Generates execution plan
5. Updates state files

**When to run:**
- Plan is >120 minutes old
- New markets available
- After code changes
- Before enabling LIVE mode

---

### 3. View Trading Dashboard
```bash
hotrade
```
**Shows:**
- Gate status
- Execution plan summary
- Current orders
- Insights and recommendations

---

### 4. Safe Execution (DRYRUN)
```bash
hoexecsafe
```
**Safety checks:**
- Health must be "healthy"
- infra_allow_trades must be true
- Gate not blocked
- Then executes plan (DRYRUN only currently)

---

### 5. Check Git Updates
```bash
cd ~/hands-off-engine
git fetch origin claude/setup-claude-cli-01DpuJGv8LbPo1Rjaa3kMM1F
git log HEAD..origin/claude/setup-claude-cli-01DpuJGv8LbPo1Rjaa3kMM1F --oneline
```
**See what Claude Code CLI pushed:**
- Latest improvements
- New features
- Documentation updates

---

### 6. Pull Latest Changes
```bash
cd ~/hands-off-engine
git pull origin claude/setup-claude-cli-01DpuJGv8LbPo1Rjaa3kMM1F
```
**After pulling:**
- Review `.claude/IMPROVEMENTS_*.md` for changes
- Test in DRYRUN first
- Then enable LIVE if safe

---

## 🎯 CRITICAL OPERATIONS

### Emergency Stop (KILLSWITCH)
```bash
# Activate killswitch (stops ALL trading)
ssh do138 "touch /root/hands-off-out/KILLSWITCH"

# Verify it's active
ssh do138 "ls /root/hands-off-out/KILLSWITCH" && echo "🔴 ACTIVE" || echo "🟢 Not active"

# Remove killswitch (restore trading)
ssh do138 "rm /root/hands-off-out/KILLSWITCH"
```

---

### Pause Autopilot
```bash
# Pause (prevent new cycles)
touch ~/hands-off/autopilot/PAUSED

# Resume
rm ~/hands-off/autopilot/PAUSED
```

---

### Check Health
```bash
./scripts/healthcheck.sh
```
**Alerts on:**
- Stale execution plan (>120 min)
- Degraded health
- Gate blocked
- Killswitch active

---

## 📊 MONITORING

### Real-Time Dashboard
```bash
# Full dashboard with analysis
python3 tools/trading_dashboard.py

# Or use alias (if configured)
hodash
```

---

### Check Execution Plan Age
```bash
cat executor/execution_plan.json | jq -r '.as_of'
# Compare to current time
date -u +"%Y-%m-%dT%H:%M:%S"
```

---

### View Current Markets
```bash
cat state/polymarket-model.json | jq -r '.markets[] | "\(.model_edge*100)% \(.question[:50])"'
```

---

### Check Mode Status
```bash
cat executor/execution_plan.json | jq -r '{mode, live_enabled, health_status, gate_blocked}'
```

---

## 🔧 TROUBLESHOOTING

### Problem: Plan is Stale
```bash
# Solution: Regenerate
ho-cycle.sh

# Verify freshness
python3 tools/trading_dashboard.py | grep "Age:"
```

---

### Problem: No Orders Despite Tradeable Markets
```bash
# Check confidence threshold
grep MIN_CONFIDENCE_THRESHOLD executor/ho_executor_plan.py
# Should show: 0.60

# Check if markets are filtered
python3 -c "
from decider.ho_decider import Decider
from pathlib import Path
d = Decider()
signals = d.load_model_signals(Path('state/polymarket-model.json'))
print(f'Loaded {len(signals)} markets after filtering')
"
```

---

### Problem: Mode is DRYRUN but Expected LIVE
```bash
# Check current mode
hoexecsafe | grep "mode\|live_enabled"

# If DRYRUN, need to enable LIVE
# See: .claude/LIVE_TRADING_OPERATIONS_GUIDE.md
```

---

### Problem: Health Degraded
```bash
# Check what's wrong
ssh do138 "/usr/local/bin/ho_snapshot.py" | jq '.health'

# Common fixes:
# - Regenerate execution plan (ho-cycle.sh)
# - Check data freshness
# - Verify droplet connectivity
```

---

## 📈 PERFORMANCE TRACKING

### View Expected Value
```bash
python3 tools/trading_dashboard.py | grep -A 5 "EXPECTED VALUE"
```

---

### Check Current P&L (if LIVE)
```bash
ssh do138 "/usr/local/bin/ho_orders_view.py"
```

---

### View Recent Orders
```bash
ssh do138 "cat /root/hands-off-out/logs/executor.log | tail -50"
```

---

## 🎮 WORKFLOW EXAMPLES

### Morning Routine
```bash
# 1. Check status
python3 tools/trading_dashboard.py

# 2. Pull latest updates
cd ~/hands-off-engine && git pull

# 3. Regenerate plan
ho-cycle.sh

# 4. Review
hotrade

# 5. Execute (DRYRUN)
hoexecsafe

# 6. If satisfied, enable LIVE (see LIVE_TRADING_OPERATIONS_GUIDE.md)
```

---

### Pre-LIVE Checklist
```bash
# 1. Fresh plan
ho-cycle.sh

# 2. Check dashboard
python3 tools/trading_dashboard.py

# 3. Verify tradeable markets > 0
# 4. Verify expected value > 0
# 5. Verify health = healthy
# 6. Verify gate not blocked
# 7. Verify no killswitch

# 8. Test in DRYRUN
hoexecsafe

# 9. Review results
# 10. Enable LIVE if satisfied
```

---

### Emergency Shutdown
```bash
# 1. Activate killswitch
ssh do138 "touch /root/hands-off-out/KILLSWITCH"

# 2. Verify stopped
python3 tools/trading_dashboard.py | grep "Killswitch"
# Should show: 🔴 ACTIVE

# 3. Check no new orders
ssh do138 "/usr/local/bin/ho_orders_view.py"

# 4. Investigate issue
# 5. Fix problem
# 6. Remove killswitch when ready
ssh do138 "rm /root/hands-off-out/KILLSWITCH"
```

---

## 🔐 SAFETY REMINDERS

✅ **ALWAYS:**
- Check dashboard before trading
- Regenerate plan if >120 min old
- Test in DRYRUN first
- Verify expected value is positive
- Monitor health status

❌ **NEVER:**
- Trade with stale data (>12 hours)
- Bypass safety gates
- Ignore degraded health
- Trade expired markets
- Exceed risk limits

⚠️ **BE CAREFUL:**
- Time decay on near-expiration markets
- Concentration risk (too many similar markets)
- Mode switching (DRYRUN ↔ LIVE)
- Manual overrides (break automation)

---

## 📚 DOCUMENTATION INDEX

**Quick Reference:**
- This file: `.claude/QUICK_OPS_GUIDE.md`

**Detailed Guides:**
- `.claude/LIVE_TRADING_OPERATIONS_GUIDE.md` - Full LIVE trading ops
- `.claude/ACTIVE_OPPORTUNITIES_ANALYSIS.md` - Market analysis
- `.claude/IMPROVEMENTS_2025-11-26.md` - Recent fixes

**System Status:**
- `.claude/CLAUDE_CODE_SYSTEM_STATUS.md` - Full system overview

**Development:**
- `.claude/HANDOFF_TO_CHATGPT_MODEL_IMPROVEMENTS.md` - Model upgrade plan

---

## 🆘 GETTING HELP

**Documentation:**
```bash
# List all guides
ls -lh .claude/*.md

# Read specific guide
cat .claude/LIVE_TRADING_OPERATIONS_GUIDE.md | less
```

**Dashboard:**
```bash
# Shows recommendations
python3 tools/trading_dashboard.py
```

**Health Check:**
```bash
./scripts/healthcheck.sh
```

**Claude Code CLI:**
- Create GitHub issue with @claude_cli tag
- Include output from `python3 tools/trading_dashboard.py`
- Include recent commits: `git log -5 --oneline`

---

**Last Updated:** 2025-11-26
**Version:** 1.0
**Maintainer:** Claude Code CLI
