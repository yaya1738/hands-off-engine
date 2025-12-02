# What's Not Autonomous Yet - Quick Reference

**Last Updated:** 2025-12-01  
**Companion to:** `AUTONOMOUS_GAPS_ANALYSIS.md` (detailed analysis)  
**Purpose:** Quick lookup for "why isn't X happening automatically?"

---

## TL;DR - The Big Gaps

| What | Status | Why Not Auto | How to Fix |
|------|--------|--------------|------------|
| Risk Model V1 Docs | Pending | Needs strategic decision | Create `docs/RISK_MODEL_V1.md` |
| Telegram Execution Notifications | Missing | Not implemented | Add `notify_execution_plan.py` |
| Daily Optimization Cycle | Queued | Waiting trigger | Run manually or check health |
| Test Task from CLI | Queued | Unclear requirements | Clarify what to test |
| Part 3 UI Connector | Stubbed | Complex implementation | Complete `part3_connector_stub.py` |
| Live Trading | DRYRUN Only | Safety by design | User must enable LIVE mode |
| MCP Verification | Not Done | One-time check needed | Test MCP tools once |
| Code Review Automation | TODO | Not implemented | Implement in `coordination_agent.py` |

---

## By User Question

### "Why am I not getting execution plan notifications?"
**Answer:** Telegram notification layer not implemented yet.

**What exists:**
- ✅ Execution plans generated (`executor/execution_plan.json`)
- ✅ Decisions made (`decider/decisions.json`)
- ❌ Telegram push notification

**To fix:** Implement `termux-hands-off/agent/notify_execution_plan.py` (Priority 1)

---

### "Why isn't the daily optimization running?"
**Answer:** It's queued but waiting for health check or manual trigger.

**Check:**
```bash
cat state/autonomous_task_queue.json
```

**To execute manually:**
```bash
./scripts/healthcheck.sh
python3 scripts/autonomous_optimization.py  # If it exists
```

---

### "Why do I still need to approve things?"
**Answer:** By design - risky changes require human approval.

**Auto-applied (no approval needed):**
- Log cleanup
- Metrics collection
- Documentation updates
- Health checks
- Non-critical bug fixes

**Requires approval:**
- Trading parameters
- Risk limits
- Capital allocation
- Strategy changes
- Configuration changes
- Live trading activation

**Check pending approvals:**
```bash
cat state/approval_queue.json
# Or via Telegram: /pending
```

---

### "Why isn't live trading happening?"
**Answer:** DRYRUN mode is default for safety.

**Current state:**
- ✅ DRYRUN execution works
- ✅ Safety checks in place
- ❌ LIVE mode disabled by policy

**To enable (requires approval):**
1. User must explicitly approve LIVE mode
2. System validates all safety checks
3. Starts with small positions (baby_mode)
4. Gradually scales based on performance

---

### "Why are there so many TODOs in the code?"
**Answer:** 35 TODOs representing future enhancements and unfinished features.

**Breakdown:**
- **13 TODOs** - Spark Plug Part 3 UI connector
- **6 TODOs** - Memory kernel system
- **4 TODOs** - Trading auto-activation and credit tracking
- **3 TODOs** - Telegram API integration
- **9 TODOs** - Miscellaneous (metrics, review, tooling)

**Not all are urgent** - many are "nice to have" vs critical path.

---

### "Why isn't Part 3 (UI connector) done?"
**Answer:** Complex implementation, currently stubbed.

**Missing pieces:**
1. Unified UI (web or terminal)
2. Per-source input handling
3. Per-target output delivery
4. Kernel sync checking
5. Desync repair logic
6. Contraction engine trigger

**Impact:** Advanced Spark Plug features unavailable

**Workaround:** Use existing file-based workflows

---

### "Why do tasks sit in the queue?"
**Answer:** Some tasks need clarification, others wait for health/triggers.

**Example stuck task:**
- "Test task from CLI" - Unclear what to test
- "Daily optimization cycle" - Waiting for health check pass

**To unstick:**
1. Clarify vague tasks via Telegram
2. Check health status: `./scripts/healthcheck.sh`
3. Manually trigger if needed

---

### "Why isn't the Risk Model V1 documented?"
**Answer:** Strategic decision needed from user.

**What's needed:**
- Max position size per market
- Bankroll percentage caps
- Confidence thresholds
- Circuit breaker rules
- Drawdown limits

**Blocker:** User (Yair) needs to decide risk tolerance parameters

**Once decided:** Create `docs/RISK_MODEL_V1.md` → unlocks Tier 1 roadmap

---

## By System Component

### Alpha Model
**Status:** ⚠️ Evolving  
**Not Auto:** Model parameters, feature selection  
**Requires:** Strategic decisions on data sources and weights

### Decider
**Status:** ⚠️ Partially exists  
**Not Auto:** Formal V1 specification  
**Requires:** Document decision rules and sizing logic

### Executor
**Status:** ✅ DRYRUN works, ❌ LIVE blocked  
**Not Auto:** Live trading mode (by design)  
**Requires:** User approval + safety validation

### Notifications
**Status:** ❌ Telegram push not implemented  
**Not Auto:** Code doesn't exist yet  
**Requires:** Implementation (~50-100 lines)

### Memory Kernels
**Status:** ⚠️ Partially stubbed  
**Not Auto:** Contraction engine, compression, search  
**Requires:** Complex implementation

### Part 3 UI
**Status:** ❌ Stubbed  
**Not Auto:** Large implementation effort  
**Requires:** Multi-component development

---

## By Impact Level

### High Impact, Not Yet Done
1. **Telegram execution notifications** - User doesn't see plans
2. **Risk Model V1 docs** - Blocks Tier 1 completion
3. **Decider V1 formalization** - Unclear decision logic
4. **Daily optimization execution** - Queued, not running

### Medium Impact, Not Yet Done
1. **Price band integration** - Execution plans missing current odds
2. **AI Intake commands** - No /status, /risk, /alpha yet
3. **Memory kernel contraction** - Advanced learning blocked
4. **Code review automation** - Manual PR review needed

### Low Impact, Not Yet Done
1. **Risk cap visibility** - Don't see which checks failed
2. **Credit tracking** - Signal marketplace feature
3. **Test task clarification** - Vague requirement
4. **MCP verification** - One-time sanity check

---

## How to Check Status

### Check Coordination Tasks
```bash
cat ai/coordination/status.json | jq '.pending_tasks'
```

### Check Autonomous Queue
```bash
cat state/autonomous_task_queue.json | jq '.tasks'
```

### Check Approval Queue
```bash
cat state/approval_queue.json | jq '.pending'
```

### Count TODOs
```bash
grep -r "TODO\|FIXME" --include="*.py" --include="*.sh" . | wc -l
```

### Check Cron Jobs (What IS running)
```bash
crontab -l | grep HANDS-OFF
```

---

## What to Do About It

### As a User
1. **Use Telegram** - Check `/pending` regularly
2. **Clarify vague tasks** - Respond to requests for details
3. **Approve risky changes** - Review and `/approve` or `/reject`
4. **Provide strategic input** - Risk tolerance, capital allocation

### As an AI Agent
1. **Check coordination status** - See what's assigned to you
2. **Process task queue** - Execute tasks you can handle
3. **Use approval system** - Propose risky changes, don't force them
4. **Update gaps doc** - When you fill a gap, document it

### As a Developer
1. **Prioritize by impact** - High-impact gaps first
2. **Close TODOs** - When you implement something, remove the TODO
3. **Document decisions** - Especially for strategic items
4. **Test autonomously** - Ensure new features don't need manual triggers

---

## Quick Wins (Easy to Fix)

These gaps can be closed quickly:

1. ✅ **Clarify "Test task"** - Ask user what to test → execute or remove
2. ✅ **Trigger optimization** - Run manually or fix health check
3. ✅ **Document Risk V1** - User decides params → write doc
4. ✅ **Add Telegram notify** - 50-100 lines of code
5. ✅ **MCP verification** - One-time test of git-status via MCP

---

## Related Docs

- **Detailed Analysis:** `docs/AUTONOMOUS_GAPS_ANALYSIS.md`
- **What's Fixed:** `docs/AUTONOMOUS_BOTTLENECKS_RESOLVED.md`
- **User Interface:** `USER_INTERFACE.md`
- **Approval System:** `ai/README_APPROVAL_SYSTEM.md`
- **Roadmap:** `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`

---

**Remember:** Not everything SHOULD be autonomous. Some decisions (risk, capital, strategy) intentionally require human approval. The goal is to automate the routine, not remove human judgment.
