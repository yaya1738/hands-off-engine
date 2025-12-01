# Automation System Troubleshooting Guide

**Last Updated:** 2025-12-01
**Version:** 1.0

---

## Quick Diagnostics

### 1. Check System Status

```bash
# Check if automation components are running
python3 tests/test_automation_validation.py -v

# Quick status check
cd /home/runner/work/hands-off-engine/hands-off-engine
python3 -c "from autonomous.absolute_directive import get_master; print(f'Master: {get_master()}')"
```

### 2. Check State Files

```bash
# Verify state directory structure
ls -la state/

# Check coordination status
cat ai/coordination/status.json | python3 -m json.tool

# Check AI nexus state
cat state/ai_nexus_state.json | python3 -m json.tool
```

### 3. Check for Lock Files

```bash
# Check for emergency stops
ls -la state/*STOP* state/*lock 2>/dev/null

# Check for circuit breakers
ls -la state/circuit_breaker.lock 2>/dev/null
```

---

## Common Issues and Solutions

### Issue: "Permission denied: /root/hands-off-engine/state"

**Symptom:** Code tries to access `/root/hands-off-engine/state` but fails

**Cause:** Hardcoded path in code expects specific directory structure

**Solution:**
```bash
# Set environment variable to point to correct state directory
export HANDS_OFF_STATE_DIR="/home/runner/work/hands-off-engine/hands-off-engine/state"

# Or run from the repo root
cd /home/runner/work/hands-off-engine/hands-off-engine
```

**Fixed In:** `absolute_directive.py` now uses dynamic path resolution

---

### Issue: Tests Failing with Import Errors

**Symptom:** `ModuleNotFoundError` when running tests

**Cause:** Missing Python dependencies

**Solution:**
```bash
# Install test dependencies
pip3 install pytest

# Install AI runner dependencies (if needed)
pip3 install openai anthropic requests
```

---

### Issue: Cascade System Not Working

**Symptom:** `cascade_directive()` fails or produces errors

**Diagnosis:**
```bash
# Test cascade manually
python3 -c "
from autonomous.absolute_directive import cascade_directive
result = cascade_directive('Test')
print(f'Status: {result[\"status\"]}')
print(f'Levels touched: {len(result[\"levels_touched\"])}')
"
```

**Expected Output:**
```
Status: complete
Levels touched: 8
```

**Solution:** If it fails, check:
1. State directory is writable
2. JSON files are valid
3. No permission issues

---

### Issue: AI Coordination Not Processing Messages

**Symptom:** Messages in `ai/coordination/messages.jsonl` not being processed

**Diagnosis:**
```bash
# Check coordination status
cat ai/coordination/status.json | grep -A 10 "pending_tasks"

# Check if coordination agent is in autonomous mode
cat ai/coordination/status.json | grep -A 5 "autonomous_mode"
```

**Solution:**
```bash
# Ensure autonomous mode is enabled
# Edit ai/coordination/status.json and verify:
{
  "autonomous_mode": {
    "copilot": true,
    "claude-code": true,
    "enabled": "2025-11-23T03:31:00Z"
  }
}
```

---

### Issue: Trading Pipeline Not Running

**Symptom:** No new entries in `state/hands_off_summary.json`

**Diagnosis:**
```bash
# Test pipeline manually
python3 ho_autoloop.py --state-dir state

# Check for errors
echo $?  # Should be 0 if successful
```

**Common Causes:**
1. **Balance too low** - Pipeline skips when balance < $10
2. **Missing data** - No `polymarket-compact.json` in state/
3. **DRYRUN disabled** - Pipeline requires DRYRUN mode

**Solution:**
```bash
# Check balance
cat state/polymarket-compact.json | grep -i balance

# Verify DRYRUN mode
grep -r "DRYRUN" ho_autoloop.py

# Force run with no fetch
python3 ho_autoloop.py --no-fetch
```

---

### Issue: Circuit Breaker Triggered

**Symptom:** Trading stopped, `state/circuit_breaker.lock` exists

**Diagnosis:**
```bash
# Check circuit breaker status
ls -la state/circuit_breaker.lock
cat state/circuit_breaker.lock 2>/dev/null | python3 -m json.tool
```

**Solution:**
```bash
# Review why circuit breaker triggered
cat logs/circuit_breaker.jsonl | tail -10

# If safe to continue, reset:
rm state/circuit_breaker.lock

# Or via Telegram (when integrated):
/approve reset-circuit-breaker
```

**Circuit breaker triggers when:**
- Daily loss > 5% of bankroll
- 3+ consecutive losing trades
- API errors > 3 in 1 hour
- Unexpected state file corruption
- Balance mismatch > 10%

---

### Issue: LIVE Trading Enabled Accidentally

**Symptom:** Fear that LIVE trading might be enabled

**Diagnosis:**
```bash
# Check TRADING_MODE environment variable
echo $TRADING_MODE

# Check for LIVE approval file
ls -la state/trading_approval.json 2>/dev/null

# Grep code for LIVE mode
grep -r "TRADING_MODE.*LIVE" . --include="*.py"
```

**Solution:**
```bash
# Force DRYRUN mode
unset TRADING_MODE
rm -f state/trading_approval.json

# Verify in code
grep "DRYRUN" ho_autoloop.py executor/*.py
```

**Safety:** LIVE trading requires ALL of:
1. `TRADING_MODE=LIVE` environment variable
2. `state/trading_approval.json` file with user approval
3. Bankroll >= $50
4. Risk model validation passed

---

### Issue: AI Runner Not Processing Tasks

**Symptom:** Tasks in `ai/tasks/` not being processed

**Diagnosis:**
```bash
# Check tasks directory
ls -la ai/tasks/

# Test AI runner manually
python3 ai_runner.py process-all

# Check for errors
tail -50 logs/ai-runner.log 2>/dev/null
```

**Solution:**
```bash
# Ensure task format is correct
cat ai/tasks/example_task.json | python3 -m json.tool

# Move stuck tasks to processed
mv ai/tasks/*.json ai/tasks/processed/

# Restart AI runner
# (If running as service, restart service)
```

---

### Issue: JSON Parse Errors in State Files

**Symptom:** `JSONDecodeError` when reading state files

**Diagnosis:**
```bash
# Find invalid JSON files
for f in state/*.json; do
  python3 -m json.tool "$f" > /dev/null 2>&1 || echo "Invalid: $f"
done
```

**Solution:**
```bash
# Backup corrupted file
cp state/corrupted_file.json state/corrupted_file.json.backup

# Restore from last known good state
# (Check backups/ directory or git history)

# Or regenerate if safe to do so
# Example for coordination status:
cat > ai/coordination/status.json << 'EOF'
{
  "last_updated": "2025-12-01T18:00:00Z",
  "active_agents": ["copilot", "claude-code"],
  "autonomous_mode": {"enabled": true},
  "current_phase": "Autonomous Operation"
}
EOF
```

---

### Issue: Hardcoded Paths Breaking in Different Environments

**Symptom:** Code assumes `/root/hands-off-engine` but running elsewhere

**Diagnosis:**
```bash
# Check where code is actually running
pwd

# Find hardcoded paths
grep -r "/root/hands-off" . --include="*.py" | grep -v ".pyc"
```

**Solution:**
```bash
# Set environment variable
export HANDS_OFF_STATE_DIR="$(pwd)/state"

# Or update code to use dynamic paths
# See autonomous/absolute_directive.py for example
```

**Pattern to Use:**
```python
from pathlib import Path
import os

def _get_state_dir() -> Path:
    """Get state directory, handling different environments."""
    if "HANDS_OFF_STATE_DIR" in os.environ:
        return Path(os.environ["HANDS_OFF_STATE_DIR"])
    
    repo_root = Path(__file__).parent.parent
    return repo_root / "state"
```

---

## Health Check Checklist

Run this checklist to verify automation system health:

- [ ] **Tests Pass**: `python -m pytest tests/test_automation_validation.py -v`
- [ ] **No Lock Files**: `ls state/*lock state/*STOP* 2>/dev/null` returns empty
- [ ] **State Files Valid**: All JSON files in `state/` parse correctly
- [ ] **Coordination Active**: `ai/coordination/status.json` shows autonomous mode enabled
- [ ] **DRYRUN Enforced**: `grep DRYRUN ho_autoloop.py` shows DRYRUN mode
- [ ] **No Circuit Breakers**: `state/circuit_breaker.lock` doesn't exist
- [ ] **Cascade System Works**: `cascade_directive()` completes successfully
- [ ] **AI Runner Ready**: `ai/tasks/` and `ai/results/` directories exist

---

## Emergency Procedures

### Stop All Automation

```bash
# Create emergency stop file
touch state/EMERGENCY_STOP.lock

# Disable trading
export TRADING_MODE=SKIP

# Stop AI runner
pkill -f "ai_runner.py"

# Verify everything stopped
ps aux | grep -E "ai_runner|autoloop|moonshot"
```

### Reset to Known Good State

```bash
# Backup current state
cp -r state/ state.backup.$(date +%s)

# Restore from backup (if available)
cp -r backups/state.latest/* state/

# Or reinitialize minimal state
mkdir -p state
cat > state/knowledge.json << 'EOF'
{
  "primary_status_doc": "termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md",
  "required_reading": ["AI_POLICY.md"]
}
EOF
```

### Force DRYRUN Mode Everywhere

```bash
# Unset LIVE mode
unset TRADING_MODE
export TRADING_MODE=DRYRUN

# Remove LIVE approvals
rm -f state/trading_approval.json

# Add DRYRUN lock
touch state/FORCE_DRYRUN.lock

# Verify
grep -r "LIVE" state/ executor/
```

---

## Monitoring Commands

### Real-time Monitoring

```bash
# Watch state directory changes
watch -n 5 'ls -lt state/*.json | head -10'

# Monitor logs (if available)
tail -f logs/*.log

# Watch for new AI tasks
watch -n 10 'ls -lt ai/tasks/'
```

### Daily Health Check

```bash
#!/bin/bash
# daily_health_check.sh

echo "=== Automation Health Check ==="
echo "Date: $(date)"
echo ""

echo "1. Tests Status:"
python -m pytest tests/test_automation_validation.py -q

echo ""
echo "2. Lock Files:"
ls state/*lock state/*STOP* 2>/dev/null || echo "None (good)"

echo ""
echo "3. Recent State Updates:"
ls -lt state/*.json | head -5

echo ""
echo "4. AI Coordination:"
cat ai/coordination/status.json | grep -A 3 "current_phase"

echo ""
echo "=== Health Check Complete ==="
```

---

## Getting Help

### Self-Diagnosis

1. Run automation tests: `python -m pytest tests/test_automation_validation.py -v`
2. Check this troubleshooting guide
3. Review recent git commits for related changes
4. Check `ai/SESSION_INSIGHTS_*.md` for recent session context

### Documentation References

- **Architecture:** `docs/AUTOMATION_SUCCESS_METRICS.md`
- **Risk Model:** `docs/RISK_MODEL_V1.md`
- **Deployment:** `ai/DEPLOYMENT_STATUS.md`
- **Development Standards:** `docs/DEVELOPMENT_STANDARDS.md`
- **User Interface:** `USER_INTERFACE.md`

### Escalation

If automation is critically broken:

1. **Stop everything** - Use emergency procedures above
2. **Backup state** - `cp -r state/ state.backup.$(date +%s)`
3. **Document the issue** - Create detailed error logs
4. **Notify via Telegram** - Alert user (when bot integrated)
5. **Create GitHub issue** - For strategic problems needing human decision

---

**Remember:** The automation system is designed to be self-healing and resilient. 
Most issues resolve automatically. This guide is for the ~1% of cases that need 
manual intervention.
