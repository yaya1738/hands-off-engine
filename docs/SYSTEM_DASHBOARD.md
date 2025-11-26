# System Dashboard - Hands-Off Engine

**Quick Reference for Monitoring and Interacting with the System**

Last Updated: 2025-11-26

---

## Quick Status Check

### One-Line Status
```bash
cd /home/runner/work/hands-off-engine/hands-off-engine && \
cat STATUS.md | head -10
```

### System Health Overview
```bash
# Check all key components
cd /home/runner/work/hands-off-engine/hands-off-engine && \
echo "=== System Phase ===" && cat ai/coordination/status.json | grep "current_phase" && \
echo "=== Active Agents ===" && cat ai/coordination/status.json | grep "active_agents" && \
echo "=== Recent Messages ===" && tail -5 ai/coordination/messages.jsonl
```

### Financial Status
```bash
# Check latest balance and positions
cd /home/runner/work/hands-off-engine/hands-off-engine && \
cat state/polymarket-model.json | jq '.bankroll, .positions[] | select(.size > 0)'
```

---

## Key Metrics to Monitor

### 1. System Health Indicators

| Metric | Location | Command | Healthy Range |
|--------|----------|---------|---------------|
| **System Phase** | `ai/coordination/status.json` | `cat ai/coordination/status.json \| jq '.current_phase'` | "Autonomous Operation" |
| **Active Agents** | `ai/coordination/status.json` | `cat ai/coordination/status.json \| jq '.active_agents'` | 3-4 agents |
| **Autonomous Mode** | `ai/coordination/status.json` | `cat ai/coordination/status.json \| jq '.autonomous_mode.enabled'` | true |
| **Last Updated** | `ai/coordination/status.json` | `cat ai/coordination/status.json \| jq '.last_updated'` | < 24 hours ago |

### 2. Trading Metrics

| Metric | Location | Command | Notes |
|--------|----------|---------|-------|
| **Bankroll** | `state/polymarket-model.json` | `cat state/polymarket-model.json \| jq '.bankroll'` | Total available capital |
| **Position Count** | `state/polymarket-model.json` | `cat state/polymarket-model.json \| jq '.positions \| length'` | Active positions |
| **Daily Orders** | Audit logs | `grep "$(date +%Y-%m-%d)" logs/audit_*.jsonl \| wc -l` | Orders executed today |
| **Win Rate** | Performance metrics | `tail -100 state/performance_metrics.jsonl \| jq -s '[.[] \| select(.outcome=="win")] \| length / 100'` | Target: >55% |

### 3. AI Agent Activity

| Metric | Location | Command | Notes |
|--------|----------|---------|-------|
| **Pending Tasks** | `ai/coordination/status.json` | `cat ai/coordination/status.json \| jq '.pending_tasks[] \| select(.status=="pending")'` | Tasks waiting |
| **Completed Tasks** | `state/autonomous_tasks_completed.jsonl` | `tail -20 state/autonomous_tasks_completed.jsonl` | Recent completions |
| **Agent Messages** | `ai/coordination/messages.jsonl` | `tail -10 ai/coordination/messages.jsonl \| jq '.'` | Inter-agent comms |
| **Approval Queue** | `state/approval_queue.json` | `cat state/approval_queue.json \| jq '.pending[]'` | Needs user approval |

---

## Health Indicators Explained

### 🟢 Healthy System

**Indicators:**
- `current_phase: "Autonomous Operation"`
- All agents showing `enabled: true` in autonomous_mode
- Recent timestamp (< 24h) in status.json
- Pending tasks have assigned agents
- No critical errors in logs

**Example:**
```json
{
  "current_phase": "Autonomous Operation - PR Consolidation",
  "active_system_status": "OPERATIONAL + OPTIMIZED + PROGRESSING",
  "last_updated": "2025-11-26T12:00:00Z"
}
```

### 🟡 Attention Needed

**Indicators:**
- Approval queue has pending items > 3 days
- No recent agent messages (> 48h)
- Tasks in "in_progress" state > 7 days
- Performance metrics showing declining win rate

**What to do:**
1. Check approval queue: `cat state/approval_queue.json`
2. Review agent messages: `tail -20 ai/coordination/messages.jsonl`
3. Check for stuck tasks: `cat ai/coordination/status.json | jq '.pending_tasks[]'`

### 🔴 Critical Issues

**Indicators:**
- System phase = "Emergency" or "Halted"
- No agent activity > 72 hours
- Circuit breaker triggered (daily loss > $200)
- Multiple agents showing `enabled: false`

**What to do:**
1. **Immediately check logs:** `tail -100 logs/audit_$(date +%Y-%m-%d).jsonl`
2. **Review error messages:** `grep "ERROR" logs/*.log`
3. **Check self-healing state:** `cat state/self_healing_state.json`
4. **Contact via Telegram** if automated recovery hasn't started

---

## Common Commands

### Monitoring

```bash
# View system status
cat STATUS.md

# Check agent coordination
cat ai/coordination/status.json | jq '.'

# View recent agent messages
tail -20 ai/coordination/messages.jsonl | jq '.'

# Check latest metrics
tail -50 state/performance_metrics.jsonl | jq '.'

# Review audit trail
tail -100 logs/audit_$(date +%Y-%m-%d).jsonl | jq '.'
```

### Inspection

```bash
# View current positions
cat state/polymarket-model.json | jq '.positions[] | select(.size > 0)'

# Check pending approvals
cat state/approval_queue.json | jq '.pending[]'

# View alpha model state
cat state/polymarket-model.json | jq '.markets[] | select(.edge > 0.03)'

# Check risk model parameters
cat docs/RISK_MODEL_V1.md | grep "Max Position"
```

### Git Status

```bash
# Check for uncommitted changes
cd /home/runner/work/hands-off-engine/hands-off-engine && git status

# View recent commits
git log --oneline -10

# Check branch status
git branch -a

# Pull latest changes
git pull origin main
```

### Service Status (Droplet)

```bash
# Check if services are running (if on droplet)
systemctl status hands-off-engine
ps aux | grep python | grep -E "(ai_runner|executor|decider)"

# View service logs
journalctl -u hands-off-engine -n 50
```

---

## Troubleshooting Common Issues

### Issue: No Recent Agent Activity

**Symptoms:**
- Last message in `messages.jsonl` > 48 hours old
- No updates to `status.json`

**Diagnosis:**
```bash
# Check coordination status
cat ai/coordination/status.json | jq '.last_updated'

# Look for error messages
tail -100 logs/*.log | grep -i error

# Check if autonomous mode is enabled
cat ai/coordination/status.json | jq '.autonomous_mode'
```

**Resolution:**
1. Verify autonomous mode is enabled in configuration
2. Check GitHub Actions workflows are running
3. Review agent-specific logs for errors
4. If needed, manually trigger coordination: `touch ai/coordination/messages.jsonl`

---

### Issue: Approval Queue Building Up

**Symptoms:**
- Multiple items in `approval_queue.json`
- Pending tasks not progressing

**Diagnosis:**
```bash
# Check approval queue
cat state/approval_queue.json | jq '.pending[] | {id, created_at, description}'

# See what's blocking
cat ai/coordination/status.json | jq '.pending_tasks[] | select(.status=="pending")'
```

**Resolution:**
1. Review each pending approval
2. Use Telegram to approve/reject: `/approve <id>` or `/reject <id>`
3. Clear stale approvals (> 7 days old) with explicit decision

---

### Issue: Circuit Breaker Triggered

**Symptoms:**
- No new orders being placed
- Message about daily loss limit

**Diagnosis:**
```bash
# Check performance metrics
tail -100 state/performance_metrics.jsonl | jq 'select(.circuit_breaker_triggered)'

# Review today's trades
grep "$(date +%Y-%m-%d)" logs/audit_*.jsonl | jq '.'
```

**Resolution:**
1. Review what caused the losses
2. Circuit breaker resets automatically at midnight
3. Investigate if risk model needs adjustment
4. Check if external events (market crashes) were responsible

---

### Issue: Agent Coordination Conflicts

**Symptoms:**
- Multiple agents working on same task
- Conflicting messages in `messages.jsonl`

**Diagnosis:**
```bash
# Check task assignments
cat ai/coordination/status.json | jq '.pending_tasks[]'

# View recent agent messages
tail -30 ai/coordination/messages.jsonl | jq '.'
```

**Resolution:**
1. Identify which tasks are duplicated
2. Update `status.json` to assign clear ownership
3. Post coordination message to resolve: Add entry to `messages.jsonl`
4. Agents will self-synchronize within 1-2 hours

---

### Issue: DRYRUN/LIVE Mode Confusion

**Symptoms:**
- Uncertainty about whether trades are being executed
- Missing orders in Polymarket account

**Diagnosis:**
```bash
# Check executor mode
grep -r "LIVE\|DRYRUN" executor/*.py | head -5

# Review audit logs for mode
tail -50 logs/audit_*.jsonl | jq '.mode'
```

**Resolution:**
1. **Default is ALWAYS DRYRUN** - no real trades unless explicitly enabled
2. Check `executor/ho_executor_plan.py` for current mode
3. Audit logs will show `"mode": "DRYRUN"` for all simulated orders
4. LIVE mode requires explicit user approval and multiple safety checks

---

## Emergency Procedures

### Stop All Trading (Emergency)

```bash
# Create emergency stop flag
echo "EMERGENCY_STOP" > /tmp/emergency_stop.flag

# Disable autonomous mode
cd /home/runner/work/hands-off-engine/hands-off-engine
cat ai/coordination/status.json | jq '.autonomous_mode.enabled = false' > ai/coordination/status.json.tmp
mv ai/coordination/status.json.tmp ai/coordination/status.json

# Post emergency message
echo "{\"timestamp\":\"$(date -Iseconds)\",\"from\":\"user\",\"to\":\"all\",\"type\":\"emergency\",\"message\":\"EMERGENCY STOP - All trading halted\"}" >> ai/coordination/messages.jsonl
```

### Resume Operations

```bash
# Remove emergency flag
rm -f /tmp/emergency_stop.flag

# Re-enable autonomous mode
cd /home/runner/work/hands-off-engine/hands-off-engine
cat ai/coordination/status.json | jq '.autonomous_mode.enabled = true' > ai/coordination/status.json.tmp
mv ai/coordination/status.json.tmp ai/coordination/status.json

# Post resume message
echo "{\"timestamp\":\"$(date -Iseconds)\",\"from\":\"user\",\"to\":\"all\",\"type\":\"info\",\"message\":\"Operations resumed\"}" >> ai/coordination/messages.jsonl
```

---

## Quick Links

- **[Autonomous Operation Guide](./AUTONOMOUS_OPERATION.md)** - How the system runs without user
- **[Risk Model V1](./RISK_MODEL_V1.md)** - Position sizing and safety parameters
- **[User Interface](../USER_INTERFACE.md)** - Telegram communication protocol
- **[Research Report](../termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md)** - Canonical status and roadmap
- **[STATUS.md](../STATUS.md)** - Quick system status file

---

## Support

For issues or questions:
1. **Primary:** Telegram bot `@pm_alerts_autobot` - `/help`
2. **Strategic:** GitHub Issues - comment `/plan` for AI planning
3. **Emergency:** CLI on Termux/Droplet node

Remember: The system is designed for minimal user intervention. Most issues self-heal automatically.
