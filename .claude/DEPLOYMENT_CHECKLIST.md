# Deployment Checklist - When SSH Returns

**Status:** Network currently unreachable
**When fixed:** Run this checklist

---

## ✅ PRE-DEPLOYMENT

- [ ] SSH connectivity restored
- [ ] Can ping do138: `ping 138.68.103.156`
- [ ] Can SSH: `ssh do138 "echo test"`
- [ ] Local improvements tested

---

## 🚀 DEPLOYMENT STEPS

### Step 1: Deploy Code
```bash
./scripts/deploy_improvements.sh
```

**This will:**
- Backup existing files
- Deploy decider improvements
- Deploy executor improvements
- Deploy dashboard
- Verify deployment
- Test on remote

---

### Step 2: Verify on Remote
```bash
ssh do138 "cd /root/hands-off-engine && python3 tools/trading_dashboard.py"
```

**Check for:**
- ✅ 5-6 tradeable markets
- ✅ Expired markets filtered
- ✅ Expected value positive
- ✅ Time decay applied

---

### Step 3: Regenerate Execution Plan
```bash
ssh do138 "/usr/local/bin/ho_executor_plan.sh"
```

Or:
```bash
ssh do138 "cd /root/hands-off && ./run_cycle.sh"
```

---

### Step 4: Check Results
```bash
ssh do138 "cd /root/hands-off-engine && python3 tools/trading_dashboard.py"
```

**Expected changes:**
- 🟢 Fresh plan (<5 min old)
- ✅ 5+ orders in plan
- ✅ Health status improved
- 💰 Expected value: $1.50-2.00/cycle

---

### Step 5: Enable LIVE (If Ready)

**Pre-LIVE checklist:**
- [ ] All safety gates passing
- [ ] Expected value positive
- [ ] Position sizes reasonable
- [ ] Tested in DRYRUN
- [ ] Ready to monitor

**Enable:**
See `.claude/LIVE_TRADING_OPERATIONS_GUIDE.md` for full instructions

---

## 📊 WHAT WE'RE DEPLOYING

### Code Changes:
1. **Decider** (`decider/ho_decider.py`)
   - Market expiration detection
   - Time decay adjustment
   - Days-to-expiration calculator

2. **Executor** (`executor/ho_executor_plan.py`)
   - Confidence threshold: 0.70 → 0.60
   - Confidence-based position scaling
   - Smart rejection vs scaling

3. **Dashboard** (`tools/trading_dashboard.py`)
   - Real-time monitoring
   - Market analysis
   - Recommendations

### Expected Impact:
- **Markets unblocked:** 0 → 5-6
- **Expected value:** $0 → $1.50-2.00/cycle
- **ROI:** 0% → 6%+
- **Monthly revenue:** $0 → $45-60

---

## 🔧 TROUBLESHOOTING

### If deployment fails:
```bash
# Check SSH
ssh do138 "echo test"

# Manual copy
scp decider/ho_decider.py do138:/root/hands-off-engine/decider/
scp executor/ho_executor_plan.py do138:/root/hands-off-engine/executor/
```

### If plan generation fails:
```bash
# Check Python
ssh do138 "python3 --version"

# Check imports
ssh do138 "python3 -c 'from decider.ho_decider import Decider; print(\"OK\")'"
```

### If still issues:
1. Check logs: `ssh do138 "tail -50 /root/hands-off-out/logs/*.log"`
2. Check state: `ssh do138 "ls -lh /root/hands-off-out/state/"`
3. Revert: `ssh do138 "cd /root/hands-off-engine && git checkout HEAD~1"`

---

## 🎯 SUCCESS METRICS

After deployment, you should see:
- ✅ 5+ tradeable markets
- ✅ 5+ orders in execution plan
- ✅ Total risk: $20-30
- ✅ Expected value: $1.50-2.00
- ✅ Health status: healthy
- ✅ Dashboard recommendations minimal

---

## 📞 POST-DEPLOYMENT

**Monitor for 24 hours:**
- Run dashboard every 4 hours
- Check execution plan age
- Verify no errors in logs
- Track P&L if LIVE

**Report back:**
- Orders executed
- P&L realized
- Any issues
- Optimization ideas

---

**WHEN SSH IS BACK: RUN `./scripts/deploy_improvements.sh`** 🚀
