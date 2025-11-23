# User-System Communication Guide

**Date:** 2025-11-23  
**Purpose:** Define how communication works between you (Yair) and the Hands-Off Engine  
**Status:** Living document - evolves with system roadmap (currently Tier 1)  
**Evolution:** Communication patterns adapt as system matures through roadmap tiers

---

## Overview

The Hands-Off Engine operates autonomously to minimize your workload while keeping you informed and in control. This guide explains all communication channels between you and the system.

**This guide evolves alongside the system** - as capabilities mature, communication patterns shift from manual oversight → intelligent filtering → exception-only notifications.

**Core Philosophy:**
- System works autonomously (minimal user intervention)
- User receives important notifications (mobile-friendly)
- User can interact when desired (via simple commands)
- User stays in control (approve/reject decisions)
- **Communication adapts to system maturity level**

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
| Alpha weights | Model scoring weights | `state/polymarket-model.json` | Active |
| Telegram config | Notification credentials | `state/tg/bots/handsoff.env` | Active |
| Task queue | Manual task additions | `state/autonomous_task_queue.json` | Active |
| Risk config | Position sizing, caps, limits | Code modules (future: `state/risk_config.json`) | Planned Tier 1 |

**Note:** Risk configuration is currently handled in code. The dedicated risk config file is part of Roadmap Tier 1 (see `HANDS_OFF_RESEARCH_REPORT_2025-11-20.md` section 4.1, item 2). To adjust risk parameters now, work with AI agents via `/plan` command.

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

#### 2.3 Direct System Commands (Beyond AI Intermediaries)

**Purpose:** Direct user-to-system communication without AI mediation

**Philosophy:** As the system matures, direct command interfaces replace AI-mediated interactions for routine operations.

**Current Implementation:**
Direct commands are currently limited, with most interactions going through AI Intake. The evolution strategy progressively adds direct interfaces.

**Tier 2 Direct Commands (Planned):**

##### `/status` - Direct system query
```bash
# Via Telegram bot (future)
/status

# Response (immediate, no AI processing):
✅ System: OPERATIONAL
⏰ Last run: 2 mins ago
📊 Signals: 3 active
💰 DRYRUN mode
🔋 Health: 98%
```

##### `/risk` - Direct risk analysis
```bash
# Via Telegram bot (future)
/risk

# Response (from state files, no AI):
📊 Risk Model V1
💰 Bankroll: $1000
📈 Max per position: $50 (5%)
⚠️ Current exposure: $150 (15%)
✅ Within limits
```

##### `/alpha` - Direct model metrics
```bash
# Via Telegram bot (future)
/alpha

# Response (from metrics, no AI):
📊 Alpha Performance (7d)
🎯 Signals: 42 generated
✅ Hit rate: 64%
📈 Avg edge: 8.2%
⚡ Response time: 0.3s
```

**Tier 3 Direct Actions (Future):**

##### One-command approvals
```bash
# Direct Telegram inline button (no GitHub, no AI)
[Approve $25 bet] [Reject] [Modify]
```

##### Voice commands
```bash
# Via Telegram voice message (future)
"Approve all bets under $20"
"Pause trading for 2 hours"
"Show me today's performance"
```

##### SMS fallback
```bash
# When Telegram unavailable (future)
Text: "STATUS"
Reply: "System OK. 2 signals. DRYRUN."
```

**Configuration Files for Direct Control:**

| File | Direct User Control | No AI Required |
|------|---------------------|----------------|
| `state/user_preferences.json` | Notification thresholds, channels | Yes |
| `state/direct_commands.json` | Enabled direct commands | Yes |
| `state/auto_approve_rules.json` | Automatic approval patterns | Yes |
| `state/pause_schedule.json` | Trading pause windows | Yes |

**Implementation Roadmap:**

1. **Tier 1 (Current)**: AI-mediated via GitHub Issues
   - Commands require AI processing
   - Responses generated by LLM
   - Manual file editing for config

2. **Tier 2 (Next)**: Hybrid (direct + AI)
   - Simple queries: direct from state files
   - Complex analysis: AI-assisted
   - Telegram bot for instant commands

3. **Tier 3 (Future)**: Primarily direct
   - Most commands: instant, no AI
   - AI only for complex decisions
   - Voice, SMS, one-tap interfaces

**Obsolescence Strategy for AI Intermediaries:**

**What gets obsoleted:**
- ❌ GitHub Issues for routine status checks
- ❌ AI agents for simple queries
- ❌ Manual file editing for common adjustments
- ❌ Waiting for AI responses for metrics

**What remains:**
- ✅ AI for strategic planning
- ✅ AI for complex analysis
- ✅ AI for system improvements
- ✅ AI for edge case handling

**Migration Path:**

```
Current (Tier 1):
User → GitHub Issue → AI Agent → Response → User
Time: minutes to hours

Tier 2:
User → Telegram Command → System → Response → User
Time: seconds
(AI available for complex queries)

Tier 3:
User → Voice/One-tap → System → Auto-execute → Notification
Time: instant
(AI monitors in background, intervenes only for exceptions)
```

**Benefits of Direct Communication:**

1. **Speed**: Seconds vs minutes/hours
2. **Reliability**: No AI API dependencies
3. **Cost**: No LLM API costs for simple queries
4. **Autonomy**: System fully self-sufficient
5. **Availability**: Works even if AI services down

**User Control Granularity:**

| Tier | Command Complexity | AI Involvement | Response Time |
|------|-------------------|----------------|---------------|
| **1** | High (requires planning) | 100% | Minutes-hours |
| **2** | Medium (simple queries) | 20% | Seconds |
| **3** | Low (one-tap/voice) | 5% | Instant |

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

#### 3.3 Autonomous System Adjustments (Self-Optimization)

**Purpose:** System adapts and improves without user intervention

**Philosophy:** As trust builds, system makes routine adjustments autonomously, only notifying user of significant changes.

**Current Self-Adjustments (Tier 1):**

1. **Performance Tracking**
   - Logs all signals and outcomes
   - Calculates hit rates automatically
   - Updates `performance_metrics.jsonl`
   - No user action required

2. **Health Monitoring**
   - Detects system issues
   - Auto-restarts failed services
   - Logs problems to `state/`
   - Alerts user only if critical

3. **Data Refresh**
   - Fetches market data hourly
   - Updates state files automatically
   - Cleans up old data
   - Silent unless errors

**Planned Self-Adjustments (Tier 2):**

4. **Alpha Model Tuning**
   - Adjusts weights based on performance
   - Tests new features in shadow mode
   - Promotes working improvements
   - Notifies user of significant changes

5. **Risk Parameter Adaptation**
   - Increases limits as track record proves
   - Decreases on losing streaks
   - Adjusts to market volatility
   - User sets boundaries, system optimizes within

6. **Notification Optimization**
   - Learns user response patterns
   - Reduces noise for ignored signals
   - Prioritizes acted-upon opportunities
   - Asks for feedback quarterly

**Advanced Self-Adjustments (Tier 3):**

7. **Autonomous Execution**
   - Auto-approves proven patterns
   - Executes routine opportunities
   - Only asks for novel situations
   - User reviews post-execution reports

8. **Market Adaptation**
   - Shifts focus to profitable markets
   - Reduces activity in unprofitable ones
   - Discovers new opportunities
   - User sets strategy, system implements

9. **Cost Optimization**
   - Minimizes API costs automatically
   - Caches frequently accessed data
   - Optimizes execution timing
   - Reports savings to user

**Configuration for Autonomy:**

```json
// state/autonomy_config.json (future)
{
  "auto_adjustments": {
    "alpha_tuning": {
      "enabled": true,
      "max_weight_change": 0.1,
      "require_approval_above": 0.2
    },
    "risk_adaptation": {
      "enabled": true,
      "max_increase": 1.2,
      "max_decrease": 0.8,
      "notify_on_change": true
    },
    "notification_learning": {
      "enabled": true,
      "min_samples": 50,
      "confidence_threshold": 0.8
    },
    "autonomous_execution": {
      "enabled": false,  // Tier 3
      "patterns": ["high_confidence_small_size"],
      "max_daily_auto_trades": 5
    }
  }
}
```

**User Oversight Levels:**

| Adjustment Type | Tier 1 | Tier 2 | Tier 3 |
|----------------|--------|--------|--------|
| Performance tracking | Auto (silent) | Auto (silent) | Auto (silent) |
| Health monitoring | Auto (alert critical) | Auto (alert critical) | Auto (alert critical) |
| Data refresh | Auto (silent) | Auto (silent) | Auto (silent) |
| Alpha tuning | Manual only | Auto (notify changes) | Auto (exception only) |
| Risk adaptation | Manual only | Auto (within bounds) | Auto (learns bounds) |
| Notification learning | None | Auto (notify quarterly) | Auto (silent) |
| Execution approval | 100% manual | Hybrid (proven auto) | 95% auto |

**Transparency Mechanisms:**

All autonomous adjustments logged to:
- `state/optimization_log.json` - What changed and why
- `state/performance_metrics.jsonl` - Impact measurements
- Daily digest to Telegram - Summary of changes
- Weekly report - Detailed analysis

**User Intervention Points:**

Even in Tier 3, user can always:
1. **Pause**: Stop all trading instantly
2. **Override**: Change any parameter
3. **Review**: See all autonomous decisions
4. **Rollback**: Revert any adjustment
5. **Limit**: Set boundaries system can't cross

**Evolution Principle:**

```
Tier 1: User decides → System executes
Tier 2: User sets bounds → System optimizes
Tier 3: User defines goals → System achieves
```

**Obsoleting AI Intermediaries:**

Instead of asking AI to adjust parameters, system:
1. Monitors performance continuously
2. Identifies improvements automatically
3. Tests changes safely
4. Implements proven improvements
5. Reports results to user

**Result:** User gets better outcomes with less effort. AI shifts from operator role to architect role.

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

### Obsolescence of AI Intermediaries

**Goal:** Shift from AI-mediated to direct user-system communication

**Current State (Tier 1):**
- Most interactions require AI (GitHub Issues → AI handler → Response)
- Complex queries need LLM processing
- Changes require manual file editing or AI assistance
- Dependency on external AI APIs

**Target State (Tier 3):**
- Direct system commands for routine operations
- AI reserved for strategic decisions only
- Self-adjusting system reduces intervention needs
- Zero dependency on AI for day-to-day operations

### Phase 1: Direct Command Interface (Tier 2)

1. **Telegram Bot Commands**
   - `/status` - Instant system health (no AI)
   - `/risk` - Live risk metrics (no AI)
   - `/alpha` - Performance stats (no AI)
   - `/pause [duration]` - Pause trading (no AI)
   - `/resume` - Resume trading (no AI)
   - **Obsoletes:** GitHub Issues for simple queries

2. **Web Dashboard**
   - Real-time system status
   - Interactive config editor
   - Performance visualizations
   - One-click parameter adjustments
   - **Obsoletes:** Manual file editing, AI for config help

3. **Smart Notifications**
   - Inline approval buttons
   - Quick action shortcuts
   - Context in notification
   - No external apps needed
   - **Obsoletes:** GitHub workflows for approvals

### Phase 2: Autonomous Operations (Tier 3)

4. **Self-Adjusting Parameters**
   - System learns optimal settings
   - Auto-tunes within bounds
   - Reports changes to user
   - Manual override always available
   - **Obsoletes:** AI for parameter optimization

5. **Pattern Recognition & Auto-Approval**
   - System learns user preferences
   - Auto-approves matching patterns
   - Only asks for novel situations
   - Full transparency log
   - **Obsoletes:** Manual approval for routine trades

6. **Predictive Alerting**
   - System anticipates issues
   - Proactive notifications
   - Self-healing where possible
   - Only escalates when needed
   - **Obsoletes:** Reactive problem-solving

7. **Voice & SMS Fallback**
   - Voice commands via Telegram
   - SMS for emergencies
   - Works without internet
   - Natural language processing
   - **Obsoletes:** Text-based commands

### Phase 3: Full Autonomy (Post-Tier 3)

8. **Goal-Based Operation**
   - User sets high-level goals
   - System determines execution
   - Continuous learning
   - Quarterly strategy reviews
   - **Obsoletes:** Tactical decision-making

9. **Exception-Only Communication**
   - System handles 95%+ autonomously
   - User alerted only for exceptions
   - Weekly summary reports
   - Always-on oversight mode
   - **Obsoletes:** Daily/hourly involvement

### AI Role Evolution

**From:** AI as intermediary
```
User → AI → System
User ← AI ← System
```

**To:** AI as architect
```
User → System (direct)
User ← System (direct)
       ↓
      AI (background monitoring, strategic improvements)
```

**Remaining AI Uses:**
- Strategic planning (quarterly/annual)
- Complex market analysis
- Code improvements and debugging
- Anomaly investigation
- System architecture evolution

**Obsoleted AI Uses:**
- ~~Simple status queries~~
- ~~Parameter adjustments~~
- ~~Routine approvals~~
- ~~Daily notifications~~
- ~~Config file editing help~~

### Implementation Timeline

| Feature | Tier | ETA | AI Replacement |
|---------|------|-----|----------------|
| Telegram bot commands | 2 | Q1 | 40% of GitHub Issues |
| Web dashboard | 2 | Q2 | 60% of manual editing |
| Auto-parameter tuning | 2-3 | Q3 | 70% of optimization requests |
| Pattern auto-approval | 3 | Q4 | 80% of routine approvals |
| Voice interface | 3 | Q4+ | 50% of text commands |
| Goal-based operation | 3+ | Year 2+ | 90% of tactical decisions |

### Success Metrics

**Reduced AI Dependency:**
- GitHub Issue commands: 100/week → 5/week
- AI API calls: 500/day → 50/day
- LLM processing time: 2hrs/day → 10min/day
- User wait time: 5min avg → 5sec avg

**Increased Autonomy:**
- User approval rate: 100% → 5%
- Self-adjustments: 0% → 80%
- Auto-resolved issues: 20% → 90%
- User time required: 30min/week → 5min/week

**Maintained Control:**
- User override capability: Always 100%
- Transparency logs: 100% complete
- Rollback capability: Any change
- Emergency pause: Instant

---

## Communication Evolution Strategy

This guide evolves in tandem with the Hands-Off Engine's development roadmap. As the system progresses through its tiers, communication patterns adapt to support new capabilities.

### Tier 1: Establish Trust (Current Phase)

**System Maturity:** Building reliable foundation  
**Communication Focus:** Transparency and manual oversight

**Active Channels:**
- Telegram notifications for all execution plans (DRYRUN)
- GitHub Issues `/plan` for strategic planning
- Manual file editing for config changes
- Direct state file monitoring

**User Involvement:** High (review all opportunities, ~30 min/week)

**Evolution Trigger:** When Tier 1 complete (risk model locked, decider stable, infra hardened)

---

### Tier 2: Increase Intelligence (Planned)

**System Maturity:** Proven reliability, improving quality  
**Communication Focus:** Selective notifications, richer insights

**New Channels:**
- `/status` - Quick system health checks
- `/risk` - Risk model analysis
- `/alpha` - Model performance reports
- Daily digests (consolidated notifications)
- Performance trend alerts

**Enhanced Features:**
- Notification filtering (high-priority only)
- Weekly summary reports
- Automatic parameter suggestions

**User Involvement:** Medium (review digests, ~15 min/week)

**Evolution Trigger:** When alpha quality improves, false positive rate drops, consistent edge demonstrated

---

### Tier 3: Scale & Automate (Future)

**System Maturity:** Multi-brain orchestration, proven edge  
**Communication Focus:** Exception-only, one-tap actions

**New Channels:**
- One-tap Telegram approvals (inline buttons)
- Voice commands for quick actions
- Proactive system recommendations
- Automated execution reports (post-trade)

**Enhanced Features:**
- Exception-only notifications (system handles routine)
- Predictive alerts (opportunities before they arise)
- Automated position management
- Cross-market opportunity detection

**User Involvement:** Low (exceptions only, ~5-10 min/week)

**Evolution Trigger:** When MBOL active, cost tracking proven, multi-market scaling validated

---

### Evolution Principles

**As system capability increases:**
1. **Notification volume decreases** - More signal, less noise
2. **Action simplicity increases** - From file edits → commands → one-tap → automatic
3. **Intelligence visibility increases** - Better explanations of why system acts
4. **User control remains constant** - Always able to override or intervene

**As system trust increases:**
1. **DRYRUN → LIVE transitions** - Gradual, validated, capped
2. **Manual → Automatic approvals** - For proven patterns only
3. **Reactive → Proactive notifications** - System anticipates needs
4. **Interrupt → Digest communication** - Batched, convenient timing

**Continuous improvements:**
- Response to user feedback patterns
- Adaptation to market condition changes
- Integration of new data sources
- Enhancement of AI agent capabilities

---

### Roadmap Alignment

Communication evolution tracks the [Hands-Off Research Report](../termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md) roadmap:

| Roadmap Phase | Communication Changes | User Impact |
|---------------|----------------------|-------------|
| **Tier 1** (Current) | Foundation channels | Manual oversight, learning |
| **Tier 2** (Next) | Intelligent filtering | Selective attention |
| **Tier 3** (Future) | Exception-only | Minimal involvement |

**Update Policy:**
- This guide updates when roadmap tiers complete
- New channels documented before launch
- Deprecated channels noted with migration path
- User notified of communication changes via Telegram

**Feedback Loop:**
- User communication preferences tracked
- Notification effectiveness measured
- Channel usage monitored
- Guide refined based on actual usage

---

### Document Maintenance

**This guide will be updated when:**
1. New communication channels are added
2. Roadmap tiers complete
3. User feedback indicates needed changes
4. System capabilities materially change
5. Communication patterns prove ineffective

**Who updates:**
- AI agents (with user review)
- System (automated improvements)
- User (direct edits)

**Version history tracked in Git** - All changes auditable and reversible

---

## Troubleshooting

### Not Receiving Notifications

**Check:**
1. Telegram bot credentials in `state/tg/bots/handsoff.env`
2. Bot token and chat ID are correct
3. Test notifications manually:
   ```bash
   # Verify script exists first
   ls -la termux-hands-off/agent/ho-executor-notify.sh
   
   # If exists, run it
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

**Currently Available:**

| Goal | Method | Location |
|------|--------|----------|
| Review trading opportunities | Check Telegram | Phone |
| Request strategic plan | Post `/plan` | GitHub Issue #1 |
| Check system status | Review state files | `state/*.json` |
| Change notification settings | Edit env file | `state/tg/bots/handsoff.env` |
| See what AIs are working on | Check coordination | `ai/coordination/status.json` |
| Monitor performance | Check metrics | `state/performance_metrics.jsonl` |
| Report an issue | Create issue or comment | GitHub Issues |

**Planned (Roadmap Tier 1):**

| Goal | Method | Notes |
|------|--------|-------|
| Adjust risk limits | Edit config file | Currently in code; use `/plan` to request changes |

---

## Key Principles

1. **Async by default**: System works while you don't think about it
2. **Notify when actionable**: Only interrupt with opportunities/issues
3. **Simple decisions**: Reduce complexity, enable quick yes/no
4. **Reversible actions**: All changes tracked in Git
5. **Safe by default**: DRYRUN until proven, caps and limits enforced
6. **Continuous improvement**: System learns and optimizes itself
7. **Evolves with system**: Communication adapts as capabilities mature

---

## Related Documentation

### System Evolution
- `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md` - **Roadmap and status** (drives communication evolution)
- See **Communication Evolution Strategy** section above for how this guide tracks roadmap tiers

### Current Communication Setup
- `AI_POLICY.md` - High-level policy for AI agents
- `docs/AI_INTAKE_SETUP_GUIDE.md` - AI Intake command setup
- `docs/EXECUTION_NOTIFICATIONS.md` - Telegram notification details

### User & AI Coordination
- `.claude/USER_PROFILE.md` - Your preferences and goals
- `.claude/AI_COORDINATION_ARCHITECTURE.md` - Multi-agent coordination

---

**Last Updated:** 2025-11-23  
**Next Review:** When Roadmap Tier 1 completes  
**Owner:** System (with user review)  
**Status:** Living document - evolves with system roadmap tiers
