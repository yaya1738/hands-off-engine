# Communication Procedures: User ↔ System

**Version:** 1.0 (2025-11-23)  
**Status:** Current and Canonical

This document describes the **optimal communication procedures** between user and system for the Hands-Off Engine. It consolidates all communication channels, protocols, and best practices into a single reference.

---

## 🚀 Quick Start: How to Communicate RIGHT NOW

**Currently Active Methods:**

### 1. GitHub Issues (✅ Works Now)
**Use for:** AI planning, strategic questions, feature requests

- Go to issue #1 in this repository
- Comment with `/plan` to get AI-generated roadmap advice
- The system will automatically respond with context-aware planning

**Example:**
```
/plan
```

### 2. Claude Code CLI (✅ Using Now)
**Use for:** Deep work, debugging, code changes

- You're using it right now!
- Continue using for code changes, investigations, architectural work
- This is the current primary method until Telegram is set up

### 3. Telegram Bot (⚙️ Needs 5-Minute Setup)
**Use for:** Quick status checks, metrics, health monitoring (once set up)

**To activate (takes ~5 minutes):**
1. Message `@BotFather` on Telegram → Send `/newbot`
2. Message `@userinfobot` on Telegram → Get your chat ID
3. On your server:
   ```bash
   export TELEGRAM_BOT_TOKEN="your_token"
   export TELEGRAM_CHAT_ID="your_chat_id"
   python3 telegram/telegram_bot_listener.py
   ```
4. Text your bot: `/status`

**After setup, you'll get:**
- `/status` - System health and latest execution
- `/metrics` - 24h performance data
- `/health` - Comprehensive health check
- Automatic notifications when trades are planned

### Recommendation for This Moment

**Short term (today):**
- ✅ Use GitHub issue #1 with `/plan` for strategic planning
- ✅ Continue using Claude Code CLI for code work

**Next step (5 minutes):**
- ⚙️ Set up Telegram bot to enable mobile access
- 📱 After setup, you can check system status from your phone anytime

**Long term goal:**
- 🎯 Use Telegram for 99% of routine queries
- 🎯 Reserve CLI for rare emergencies only

---

## Overview

The Hands-Off Engine uses a **multi-channel communication architecture** designed to minimize manual intervention while maintaining full user control:

1. **Telegram** (Primary) - Bidirectional, real-time, mobile-friendly
2. **GitHub Issues** (Secondary) - AI coordination and planning
3. **Automated Notifications** (Outbound) - System status and alerts
4. **Claude Code CLI** (Emergency) - Rare, deep interventions only

---

## 1. Telegram Bot (Primary Channel)

**Purpose:** Complete system control from your phone with zero CLI needed.

**Status:** ✅ Implemented (see `telegram/telegram_command_bot.py`)

### 1.1 User → System Commands

Send these commands to your Telegram bot:

| Command | Description | Example |
|---------|-------------|---------|
| `/status` | Get full system status (health, latest execution, metrics) | `/status` |
| `/metrics` | Performance metrics for last 24 hours | `/metrics` |
| `/health` | Run comprehensive health check | `/health` |
| `/agents` | AI agent coordination status | `/agents` |
| `/approve <id>` | Approve pending change (future) | `/approve 123` |
| `/reject <id>` | Reject pending change (future) | `/reject 123` |
| `/help` | Command list and help | `/help` |

### 1.2 System → User Notifications

The system automatically sends notifications for:

- **Trade Execution Plans** - After decider generates plans
- **Health Alerts** - When issues are detected
- **Error Notifications** - When automated recovery fails
- **Weekly Reports** - Summary of performance and changes

**Example notification format:**
```
🔵 DRYRUN Execution Plan

📊 Summary: 3 orders, $75 total
⏰ 2025-11-23T03:07:42

Orders:
1. [macro] CPI drops below 2.5% by June?
   buy_yes • $25 • Edge: 10.0%
2. [crypto] Ethereum reaches $5k by Q1?
   buy_yes • $25 • Edge: 10.0%

📍 Review full plan in execution_plan.json
```

### 1.3 Setup Instructions

**Time Required:** ~5 minutes

1. **Create Bot** (via @BotFather on Telegram)
   - Send `/newbot` to @BotFather
   - Choose name: "Hands Off Engine Bot"
   - Save the token (format: `123456789:ABC...`)

2. **Get Your Chat ID** (via @userinfobot)
   - Message @userinfobot
   - Copy your chat ID (numeric value)

3. **Configure Server**
   ```bash
   export TELEGRAM_BOT_TOKEN="your_token_here"
   export TELEGRAM_CHAT_ID="your_chat_id_here"
   
   # Make permanent
   echo 'export TELEGRAM_BOT_TOKEN="..."' >> ~/.bashrc
   echo 'export TELEGRAM_CHAT_ID="..."' >> ~/.bashrc
   ```

4. **Test Connection**
   ```bash
   cd /root/hands-off-engine
   python3 telegram/telegram_bot_listener.py
   ```
   
   Then send `/status` from Telegram.

5. **Deploy as Service** (Optional, for 24/7 operation)
   ```bash
   sudo systemctl enable telegram-bot
   sudo systemctl start telegram-bot
   ```

**Full Setup Guide:** `telegram/TELEGRAM_SETUP.md`

### 1.4 Security Considerations

- Bot token is like a password - **keep it secret**
- Always set `TELEGRAM_CHAT_ID` to restrict bot to only your chat
- Without `TELEGRAM_CHAT_ID`, anyone who finds your bot can use it
- Store credentials in environment variables, not in code

---

## 2. GitHub AI Intake (Secondary Channel)

**Purpose:** AI-driven planning and coordination via GitHub issues.

**Status:** ✅ Implemented (see `.github/workflows/ai-intake.yml` and `ai/ai_intake_handler.py`)

### 2.1 How It Works

1. Comment on the AI Intake issue (default: issue #1) with a slash command
2. GitHub Action triggers automatically
3. Handler reads `AI_POLICY.md` and the research report
4. Calls OpenAI API with full context
5. Posts response back as a comment

### 2.2 Available Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/plan` | Generate roadmap-aligned plan based on current status | Comment `/plan` on issue #1 |

**Future commands** (planned):
- `/apply` - Generate and create PR with proposed changes
- `/status` - Summarize current system state
- `/risk` - Analyze risk model outputs
- `/todo` - Extract actionable items from roadmap

### 2.3 Setup Requirements

**Required GitHub Secret:**
- `OPENAI_API_KEY` - Your OpenAI API key

**Setup Steps:**
1. Navigate to: `https://github.com/yaya1738/hands-off-engine/settings/secrets/actions`
2. Create new repository secret named `OPENAI_API_KEY`
3. Set value to your OpenAI API key
4. Save

**Configuration:**
- `AI_INTAKE_ISSUE_NUMBER` environment variable (default: 1)
- Model: `gpt-4o-mini` (configurable in `ai/ai_intake_handler.py`)

### 2.4 When to Use AI Intake

**Best for:**
- Planning major changes or features
- Getting AI analysis of roadmap priorities
- Coordinating multi-agent work
- Strategic decisions requiring context awareness

**Not for:**
- Real-time status checks (use Telegram `/status` instead)
- Routine operations (use Telegram bot)
- Emergency interventions (use Claude Code CLI)

---

## 3. Automated Notifications (Outbound Only)

**Purpose:** Keep user informed without requiring manual queries.

**Status:** ✅ Implemented for execution plans (see `docs/EXECUTION_NOTIFICATIONS.md`)

### 3.1 Notification Types

| Type | Trigger | Channel | Frequency |
|------|---------|---------|-----------|
| Execution Plans | After executor runs | Telegram/IFTTT | Per pipeline run (hourly) |
| Health Alerts | Health check failures | Telegram | On detection |
| Error Notifications | Unrecoverable errors | Telegram | On occurrence |
| Weekly Reports | Scheduled | Telegram/Email | Weekly (Sunday 09:00 UTC) |

### 3.2 Configuration

**Telegram** (Primary):
- Set in `~/hands-off/state/tg/bots/handsoff.env`
- Variables: `TOKEN`, `CHAT_ID`

**IFTTT** (Optional):
- Set in `~/hands-off/ifttt.env`
- Variables: `IFTTT_WEBHOOK_KEY`, `IFTTT_EVENT_NAME`

### 3.3 Notification Scripts

- **Execution Plans:** `termux-hands-off/agent/notify_execution_plan.py`
- **Health Alerts:** `scripts/healthcheck.sh` (with Telegram integration)
- **Weekly Reports:** `scripts/weekly_report_generator.py` (future)

---

## 4. Claude Code CLI (Emergency Only)

**Purpose:** Deep debugging and architectural changes when automation can't handle it.

**Status:** Available but should be **rarely needed** (~1x/month or less)

### 4.1 When CLI IS Needed

Use Claude Code CLI only for:

1. **Catastrophic Failure**
   - All automated systems down
   - Self-healing can't recover
   - Manual intervention required

2. **Major Architectural Changes**
   - Rewriting core systems
   - Changing fundamental architecture
   - Complex refactoring

3. **Deep Debugging**
   - Issue too complex for automated agents
   - Requires human-level reasoning
   - Multi-step investigation

### 4.2 When CLI Is NOT Needed

**Don't use CLI for:**
- ❌ Status checks → Use Telegram `/status`
- ❌ Approving changes → Use Telegram `/approve`
- ❌ Getting metrics → Use Telegram `/metrics`
- ❌ Health checks → Use Telegram `/health`
- ❌ Routine operations → System handles automatically

### 4.3 CLI Launch Trigger

System will alert you via Telegram when CLI is needed:

```
🚨 CRITICAL: Automated recovery failed
Issue: [description]
Please launch Claude Code CLI for manual intervention
```

**Target:** 99% of operations via Telegram, 1% via CLI (emergencies only)

---

## 5. Communication Architecture

### 5.1 Architecture Diagram

```
                    ┌─────────────┐
                    │    USER     │
                    │   (Human)   │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │  TELEGRAM   │◄─── Primary Interface (99%)
                    │     BOT     │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌──────▼──────┐    ┌─────▼─────┐
   │ Trading │      │ Self-Healing│    │Coordination│
   │Pipeline │      │   Agent     │    │   Agent    │
   │(Hourly) │      │   (24/7)    │    │ (Events)   │
   └────┬────┘      └──────┬──────┘    └─────┬──────┘
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                    ┌──────▼──────┐
                    │   GITHUB    │◄─── AI Coordination (1%)
                    │  (AI Intake)│
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌──────▼──────┐    ┌─────▼─────┐
   │ Copilot │      │ Claude Web  │    │  ChatGPT  │
   │ Agent   │      │   Agent     │    │   Agent   │
   └─────────┘      └─────────────┘    └───────────┘

   ┌─────────────────────────────────────────────┐
   │  Claude Code CLI (EMERGENCY ONLY - <1%)     │
   └─────────────────────────────────────────────┘
```

### 5.2 Communication Flow Priority

```
User needs information/action
    │
    ├─→ Routine operation? → Telegram Bot
    │
    ├─→ AI planning needed? → GitHub AI Intake
    │
    ├─→ System notification? → Automated (no user action)
    │
    └─→ Emergency/Deep work? → Claude Code CLI
```

### 5.3 Channel Selection Guide

| Need | Channel | Why |
|------|---------|-----|
| Quick status check | Telegram `/status` | Instant, mobile-friendly |
| Performance review | Telegram `/metrics` | 24h summary, no CLI needed |
| Approve a change | Telegram `/approve` | One command, done |
| AI planning session | GitHub `/plan` | Full context, documented |
| Strategic analysis | GitHub AI Intake | Leverages GPT-4, persistent |
| Emergency debugging | Claude Code CLI | Deep access, full capabilities |

---

## 6. Best Practices

### 6.1 For Routine Operations

✅ **DO:**
- Use Telegram for all routine queries
- Let automated notifications inform you
- Trust self-healing agents to fix common issues
- Check weekly reports for comprehensive summaries

❌ **DON'T:**
- Launch CLI for status checks
- Manually monitor logs continuously
- Interrupt automated workflows unnecessarily
- Override self-healing without investigation

### 6.2 For AI Coordination

✅ **DO:**
- Use GitHub AI Intake for planning
- Document major decisions in issues
- Let coordination agent handle inter-AI communication
- Review AI-generated PRs via GitHub

❌ **DON'T:**
- Use Telegram for complex AI planning
- Mix routine operations with strategic planning
- Manually relay messages between AI agents
- Skip documentation for major changes

### 6.3 For Emergency Situations

✅ **DO:**
- Wait for system alert before launching CLI
- Document the issue and resolution
- Update automation to prevent recurrence
- Test self-healing improvements

❌ **DON'T:**
- Launch CLI at first sign of trouble
- Skip automated recovery attempts
- Make changes without understanding root cause
- Forget to update documentation after fix

---

## 7. Success Metrics

### 7.1 Current State (as of 2025-11-23)

- **CLI Usage:** ~1x/week (target: <1x/month)
- **Telegram Setup:** Available, needs user deployment
- **GitHub AI Intake:** ✅ Working
- **Automated Notifications:** ✅ Execution plans working
- **Self-Healing:** 🔄 In development

### 7.2 Target State (Zero-Touch Operation)

- **CLI Usage:** <1x/month (emergencies only)
- **Telegram Bot:** 24/7 operation, <2s response time
- **User Queries:** >90% via Telegram
- **Automated Fixes:** >95% of common issues
- **Weekly Reports:** 100% automated, actionable

### 7.3 How to Measure

Track these metrics:
1. Number of CLI sessions per month
2. Telegram commands processed per day
3. Issues auto-fixed vs. requiring manual intervention
4. User satisfaction with response times
5. Percentage of operations requiring zero manual input

---

## 8. Troubleshooting

### 8.1 Telegram Bot Not Responding

**Symptoms:** Commands sent to bot receive no response

**Debug Steps:**
1. Check if bot is running: `sudo systemctl status telegram-bot`
2. Check environment variables: `echo $TELEGRAM_BOT_TOKEN`
3. Check logs: `tail -f /var/log/telegram-bot.log`
4. Verify token with @BotFather
5. Test manually: `python3 telegram/telegram_bot_listener.py`

**Common Causes:**
- Bot service stopped
- Invalid token or chat ID
- Network connectivity issues
- Python dependencies missing

### 8.2 GitHub AI Intake Not Working

**Symptoms:** `/plan` command on issue gets no response

**Debug Steps:**
1. Check GitHub Action ran: Visit Actions tab in repo
2. Verify `OPENAI_API_KEY` secret exists
3. Check action logs for errors
4. Ensure commenting on correct issue number
5. Check rate limits on OpenAI API

**Common Causes:**
- Missing or invalid OpenAI API key
- Wrong issue number
- API rate limit exceeded
- GitHub Actions quota exceeded

### 8.3 Notifications Not Being Received

**Symptoms:** Expected notifications don't arrive

**Debug Steps:**
1. Check notification script ran: Check cron logs
2. Verify env files exist with correct credentials
3. Test manually: `python3 termux-hands-off/agent/notify_execution_plan.py`
4. Check Telegram API connectivity
5. Verify execution_plan.json exists

**Common Causes:**
- Missing env file or credentials
- Script not in cron schedule
- No execution plan generated
- Network issues to Telegram API

---

## 9. Implementation Roadmap

### Phase 1: Core Telegram (Weeks 1-2)
- [x] Telegram bot command structure
- [ ] Deploy as 24/7 service
- [ ] Test all commands end-to-end
- [ ] Document user setup process

### Phase 2: Approval System (Weeks 3-4)
- [ ] Implement approval/rejection workflow
- [ ] Create pending changes database
- [ ] Add approval notifications
- [ ] Test with real change scenarios

### Phase 3: Self-Healing Integration (Weeks 5-6)
- [ ] Self-healing agent reports to Telegram
- [ ] Auto-fix notifications
- [ ] Escalation to user when needed
- [ ] Weekly summary generation

### Phase 4: Optimization (Weeks 7-8)
- [ ] Measure communication metrics
- [ ] Optimize response times
- [ ] Add inline buttons for common actions
- [ ] Polish notification formatting

---

## 10. Related Documentation

- **Setup:** `telegram/TELEGRAM_SETUP.md` - Telegram bot setup guide
- **Notifications:** `docs/EXECUTION_NOTIFICATIONS.md` - Notification system details
- **AI Intake:** `docs/AI_INTAKE_IMPLEMENTATION_REPORT.md` - AI Intake architecture
- **Zero-Touch:** `ai/ZERO_TOUCH_ARCHITECTURE.md` - Overall vision and design
- **Coordination:** `.claude/AI_AGENT_COORDINATION_LOG.md` - Inter-agent communication

---

## 11. Maintenance

This document should be updated when:

- New communication channels are added
- Commands are added, removed, or changed
- Architecture changes significantly
- Best practices evolve based on usage
- New automation reduces manual communication needs

**Last Updated:** 2025-11-23  
**Next Review:** 2025-12-23 or when major changes occur  
**Maintainer:** System + AI agents (with human approval for major changes)

---

## Summary

The Hands-Off Engine uses a **tiered communication architecture**:

1. **Telegram** (Primary) - 99% of routine operations
2. **GitHub AI Intake** (Secondary) - AI planning and coordination
3. **Automated Notifications** (Outbound) - System status without queries
4. **Claude Code CLI** (Emergency) - <1% for deep work

**Goal:** Zero-touch operation where user is informed and in control without needing to manually query or intervene in routine operations.

**Current Status:** Core infrastructure implemented, deployment and optimization in progress.

**User Action:** Complete Telegram bot setup to enable primary communication channel.
