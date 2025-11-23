# User-System Communication Guide

**Date:** 2025-11-23  
**Purpose:** Define how communication works between you (Yair) and the Hands-Off Engine  
**Status:** Active and evolving

---

## Overview

The Hands-Off Engine operates autonomously to minimize your workload while keeping you informed and in control. This guide explains all communication channels between you and the system.

**Core Philosophy:**
- System works autonomously (minimal user intervention)
- User receives important notifications (mobile-friendly)
- User can interact when desired (via simple commands)
- User stays in control (approve/reject decisions)

---

## Communication Channels

### 1. System → User (Notifications)

#### 1.1 Telegram Notifications

**Purpose:** Real-time mobile alerts for important events

**What you receive:**
- 🔵 **Execution Plans**: Trading opportunities ready for review
- ✅ **Status Updates**: Hourly pipeline completion confirmations
- ⚠️ **Alerts**: System issues or important warnings
- 📊 **Performance**: Daily/weekly performance summaries

**Example notification:**
```
🔵 DRYRUN Execution Plan

📊 Summary: 3 orders, $75 total
⏰ 2025-11-23T05:00:00Z

Orders:
1. [macro] CPI drops below 2.5% by June?
   buy_yes • $25 • Edge: 10.0%
2. [crypto] Ethereum reaches $5k by Q1?
   buy_yes • $25 • Edge: 8.5%
3. [sports] Lakers win championship?
   buy_yes • $25 • Edge: 12.0%

📍 Review full plan in execution_plan.json
```

**Configuration:**
- **Setup file**: `~/hands-off/state/tg/bots/handsoff.env`
- **Required**: `TOKEN` (bot token) and `CHAT_ID` (your chat ID)
- **Documentation**: `docs/EXECUTION_NOTIFICATIONS.md`

**How to set up:**
1. Create bot via @BotFather on Telegram
2. Get bot token
3. Send message to your bot
4. Get chat ID from `https://api.telegram.org/bot<TOKEN>/getUpdates`
5. Save credentials to env file

---

### 2. User → System (Commands)

#### 2.1 GitHub Issues (AI Intake)

**Purpose:** High-level planning and task delegation

**How it works:**
1. You post a command on GitHub Issue #1 (AI Intake)
2. GitHub Action triggers automatically
3. AI handler processes your command
4. Response posted back as comment

**Available commands:**

##### `/plan`
Generate a roadmap-aligned plan for next steps

**Usage:**
```
/plan
```

**What it does:**
- Reads current AI_POLICY.md
- Reads HANDS_OFF_RESEARCH_REPORT
- Analyzes current roadmap priorities
- Generates concrete implementation steps
- Posts plan as issue comment

**Example response:**
```
🤖 AI Intake – Plan

Based on the current roadmap (Tier 1 priorities):

1. Lock Risk Model V1
   - Define simple, conservative formulas
   - Document in docs/RISK_MODEL_V1.md
   - Files: state/risk_config.json, decider/

2. Improve Alpha Quality
   - Reduce placeholder signal usage (currently 92.8%)
   - Add more market-specific features
   - Files: alpha/, state/polymarket-model.json

3. Harden Infra Safety
   - Add DRYRUN/LIVE toggle validation
   - Implement per-order caps
   - Files: executor/, state/
```

**Future commands (planned):**
- `/status` - Get current system status
- `/risk` - Analyze risk model outputs
- `/alpha` - Review alpha model performance
- `/execute <task>` - Delegate specific task to AI

**Configuration:**
- **Workflow file**: `.github/workflows/ai-intake.yml`
- **Handler script**: `ai/ai_intake_handler.py`
- **AI Intake issue**: GitHub Issue #1 (configurable)
- **Documentation**: `docs/AI_INTAKE_SETUP_GUIDE.md`

---

#### 2.2 Direct File Editing

**Purpose:** Direct control over system configuration

**When to use:**
- Adjust risk parameters
- Update alpha model weights
- Modify notification settings
- Change execution rules

**Key configuration files:**

| File | Purpose | Location | Status |
|------|---------|----------|--------|
| Risk config | Position sizing, caps, limits | `state/risk_config.json` | Planned (see Roadmap Tier 1) |
| Alpha weights | Model scoring weights | `state/polymarket-model.json` | Active |
| Telegram config | Notification credentials | `state/tg/bots/handsoff.env` | Active |
| Task queue | Manual task additions | `state/autonomous_task_queue.json` | Active |

**Note:** Risk configuration is currently handled in code. The dedicated risk config file is part of Roadmap Tier 1 (see `HANDS_OFF_RESEARCH_REPORT_2025-11-20.md` section 4.1, item 2). Until then, risk parameters are embedded in the alpha/risk modules.

**How to edit:**
1. Clone repository or edit on GitHub web
2. Modify configuration file
3. Commit and push changes
4. System picks up changes on next run

**Safety:**
- All changes tracked in Git (reversible)
- System validates configs before use
- DRYRUN mode prevents real money risk
- AI agents can review your changes

---

### 3. Bidirectional (Coordination)

#### 3.1 AI Coordination Files

**Purpose:** Multi-agent collaboration (AI-to-AI primarily)

**Location:** `ai/coordination/`

**Files:**
- `status.json` - Current agent states and active tasks
- `messages.jsonl` - Message log between agents
- `handoffs.json` - Task handoff tracking

**Your role:**
- **Read**: Check what AI agents are working on
- **Write (optional)**: Add tasks or adjust priorities
- **Monitor**: Ensure agents are aligned with your goals

**Example status.json:**
```json
{
  "last_updated": "2025-11-23T05:00:00Z",
  "active_agents": ["copilot", "claude-code", "chatgpt"],
  "autonomous_mode": {
    "enabled": true,
    "note": "Agents serve Yair without manual prompting"
  },
  "pending_tasks": [
    {
      "id": "alpha-optimization",
      "assigned_to": "auto",
      "status": "in_progress",
      "priority": "high"
    }
  ]
}
```

**Documentation:** `.claude/AI_COORDINATION_ARCHITECTURE.md`

---

#### 3.2 State Files (System Truth)

**Purpose:** Canonical current state of the system

**Location:** `state/`

**Key files:**
- `knowledge.json` - Central knowledge base
- `performance_metrics.jsonl` - Historical performance
- `autonomous_task_queue.json` - Pending automated tasks
- `optimization_log.json` - System improvements log

**Your role:**
- **Read**: Understand current system state
- **Monitor**: Track performance over time
- **Review**: Ensure system is working as expected

**Access:**
- Via GitHub web interface
- Via git clone locally
- Via AI agent queries

---

## Communication Workflows

### Workflow 1: Review Trading Opportunity

**System side:**
1. Hourly: Fetch market data
2. Run alpha models (score opportunities)
3. Apply risk filters
4. Generate execution plan
5. Send Telegram notification

**Your side:**
1. Receive notification on phone
2. Review opportunities (1-2 minutes)
3. Decide: approve, skip, or modify
4. (Future) One-tap approve via Telegram
5. (Current) Approve by editing configs or messaging AI

**Frequency:** As opportunities arise (varies by market conditions)

---

### Workflow 2: Request Strategic Plan

**Your side:**
1. Open GitHub Issue #1
2. Post comment: `/plan`
3. Wait ~30 seconds

**System side:**
1. GitHub Action triggers
2. AI loads context (policy, roadmap, state)
3. AI generates plan aligned with priorities
4. Posts plan as comment

**Your side:**
5. Review plan
6. Approve, modify, or delegate to AI agents

**Frequency:** As needed (weekly, or when direction needed)

---

### Workflow 3: Monitor System Health

**System side:**
1. Continuous: Run health checks
2. Track performance metrics
3. Log to state files
4. Alert on issues (via Telegram)

**Your side:**
1. Receive alerts if issues arise
2. (Optional) Check GitHub for detailed logs
3. (Optional) Review state files
4. Let system self-heal or instruct AI agents

**Frequency:** Passive (alerts only when needed)

---

### Workflow 4: Adjust System Parameters

**Your side:**
1. Identify parameter to change (e.g., risk limits)
2. Option A: Edit file directly on GitHub
3. Option B: Ask AI via `/plan` or issue comment
4. Commit changes

**System side:**
1. Detect config change on next run
2. Validate new parameters
3. Apply changes
4. Log update

**Frequency:** Rare (as strategy evolves)

---

## Information Flow

```
┌─────────────────────────────────────────────────────────┐
│                      YOU (Yair)                         │
│                                                         │
│  • Review notifications (Telegram)                     │
│  • Post commands (GitHub Issues)                       │
│  • Edit configs (GitHub files)                         │
│  • Monitor status (state files)                        │
└────────┬──────────────────────────────┬────────────────┘
         │                              │
         │ Commands & Config            │ Notifications & Status
         ▼                              ▼
┌─────────────────────────────────────────────────────────┐
│              HANDS-OFF ENGINE                           │
│                                                         │
│  Autonomous Components:                                │
│  • Data fetchers (hourly)                              │
│  • Alpha models (scoring)                              │
│  • Risk engine (validation)                            │
│  • Decider (planning)                                  │
│  • Executor (DRYRUN/LIVE)                              │
│  • Health monitor (continuous)                         │
│                                                         │
│  AI Agents:                                            │
│  • Copilot (autonomous improvements)                   │
│  • Claude Code (implementation)                        │
│  • ChatGPT (planning)                                  │
└─────────────────────────────────────────────────────────┘
         │                              │
         │ Market data                  │ Trades (future LIVE)
         ▼                              ▼
┌─────────────────────────────────────────────────────────┐
│              EXTERNAL SYSTEMS                           │
│                                                         │
│  • Polymarket API (market data)                        │
│  • Price feeds (crypto, stocks)                        │
│  • Trading accounts (future)                           │
└─────────────────────────────────────────────────────────┘
```

---

## Expected Time Commitment

**Daily:**
- Review Telegram notifications: **1-2 minutes**
- Approve/skip opportunities: **0-5 minutes**

**Weekly:**
- Check GitHub issues: **5 minutes** (optional)
- Review performance metrics: **5 minutes** (optional)

**Monthly:**
- Strategic planning (`/plan`): **10-15 minutes**
- Review and adjust parameters: **15-30 minutes**

**Total weekly commitment: ~10-30 minutes** (system handles rest)

---

## Communication Preferences

Based on `.claude/USER_PROFILE.md`:

### Your Preferences:
- **Notification style**: Mobile-friendly, concise
- **Frequency**: As needed, not excessive
- **Detail level**: Summary on phone, details in logs
- **Alerts**: Only for important issues or opportunities
- **Decision making**: Simple yes/no, minimize complexity
- **Management time**: Near zero (system handles)

### System Behavior:
- Operates autonomously
- Notifies only when actionable
- Provides summaries, not raw data
- Minimizes interruptions
- Self-improves over time

---

## Future Enhancements

### Planned improvements:

1. **One-Tap Approval**
   - Telegram inline buttons
   - Approve/reject trades from phone
   - No need to open GitHub or configs

2. **Richer Notifications**
   - Daily performance digest
   - Weekly summary reports
   - Market opportunity alerts

3. **More Commands**
   - `/status` - System health check
   - `/risk` - Risk analysis
   - `/alpha` - Model performance
   - `/execute <task>` - Delegate work

4. **Voice Interface** (future)
   - Voice commands via Telegram
   - Spoken notifications
   - Hands-free operation

5. **Dashboard** (future)
   - Web viewer for state
   - Visual performance charts
   - Real-time system status

---

## Troubleshooting

### Not Receiving Notifications

**Check:**
1. Telegram bot credentials in `state/tg/bots/handsoff.env`
2. Bot token and chat ID are correct
3. Test notifications manually:
   ```bash
   # If script exists (verify path first)
   termux-hands-off/agent/ho-executor-notify.sh
   
   # Or test directly with Python
   python3 termux-hands-off/agent/notify_execution_plan.py
   ```
4. Check Telegram bot is not blocked

**Fix:**
- Verify credentials with Telegram API
- Recreate bot if needed
- Check notification scripts are running

---

### AI Intake Not Responding

**Check:**
1. Command posted on correct issue (#1)
2. Command starts with `/` (e.g., `/plan`)
3. GitHub Actions workflow is enabled
4. `OPENAI_API_KEY` secret is set

**Fix:**
- Check Actions tab for workflow run status
- Verify secrets in repo settings
- Ensure workflow file is on main branch

---

### System Not Running Autonomously

**Check:**
1. Cron jobs are active (Termux)
2. Orchestrator is running
3. Recent performance metrics exist
4. Check logs for errors

**Fix:**
- Review `termux-hands-off/autopilot/` scripts
- Check `state/autonomous_task_queue.json`
- Review `.claude/PRODUCTION_STATUS.md`

---

## Quick Reference

### I want to...

| Goal | Method | Location |
|------|--------|----------|
| Review trading opportunities | Check Telegram | Phone |
| Request strategic plan | Post `/plan` | GitHub Issue #1 |
| Check system status | Review state files | `state/*.json` |
| Adjust risk limits | Edit config | `state/risk_config.json` |
| Change notification settings | Edit env file | `state/tg/bots/handsoff.env` |
| See what AIs are working on | Check coordination | `ai/coordination/status.json` |
| Monitor performance | Check metrics | `state/performance_metrics.jsonl` |
| Report an issue | Create issue or comment | GitHub Issues |

---

## Key Principles

1. **Async by default**: System works while you don't think about it
2. **Notify when actionable**: Only interrupt with opportunities/issues
3. **Simple decisions**: Reduce complexity, enable quick yes/no
4. **Reversible actions**: All changes tracked in Git
5. **Safe by default**: DRYRUN until proven, caps and limits enforced
6. **Continuous improvement**: System learns and optimizes itself

---

## Related Documentation

- `AI_POLICY.md` - High-level policy for AI agents
- `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md` - Status and roadmap
- `docs/AI_INTAKE_SETUP_GUIDE.md` - AI Intake command setup
- `docs/EXECUTION_NOTIFICATIONS.md` - Telegram notification details
- `.claude/USER_PROFILE.md` - Your preferences and goals
- `.claude/AI_COORDINATION_ARCHITECTURE.md` - Multi-agent coordination

---

**Last Updated:** 2025-11-23  
**Owner:** System (with user review)  
**Status:** Living document (evolves with system)
