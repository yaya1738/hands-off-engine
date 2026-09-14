# Autonomous Architecture - Visual Guide

**Purpose:** Visual representation of autonomous operation flow  
**Audience:** Developers and AI agents working on the system  
**Status:** Current state + target state

---

## Current State (As Implemented)

```
┌────────────────────────────────────────────────────────────────┐
│                        USER (Yair Siegel)                      │
│                   Current Interface: CLI + GitHub              │
└──────────────────────────┬─────────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
   ┌───────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
   │   GitHub    │  │    CLI    │  │  Telegram │
   │  Workflows  │  │  (Manual) │  │(Not Setup)│
   │  ✅ Active  │  │ ✅ Works  │  │  🔴 None  │
   └───────┬─────┘  └─────┬─────┘  └───────────┘
           │               │
   ┌───────▼─────┐  ┌─────▼──────────────────────────┐
   │ Auto-Merge  │  │  Autonomous Scripts (Exist)    │
   │  Workflow   │  │  • self_healing_agent.py       │
   │  ✅ Active  │  │  • coordination_agent.py       │
   └─────────────┘  │  • telegram_command_bot.py     │
                    │  • autonomous_phase_manager.py │
                    │  🔴 Not Running as Services    │
                    └────────────────────────────────┘
```

**Key Issue:** Scripts exist but not deployed as 24/7 services

---

## Target State (Per Documentation)

```
┌────────────────────────────────────────────────────────────────┐
│                        USER (Yair Siegel)                      │
│                  PRIMARY: Telegram (99% ops)                   │
│                  BACKUP: CLI (1% - emergencies)                │
└──────────────────────────┬─────────────────────────────────────┘
                           │
                           │
                ┌──────────▼──────────┐
                │   Telegram Bot      │◄──── Commands In
                │   (24/7 Service)    │───── Responses Out
                └──────────┬──────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌──────▼─────────┐  ┌────▼──────────┐
│ Self-Healing   │  │ Coordination   │  │    GitHub     │
│    Agent       │  │     Agent      │  │   Workflows   │
│ (24/7 Service) │  │ (24/7 Service) │  │   (Events)    │
└───────┬────────┘  └──────┬─────────┘  └────┬──────────┘
        │                  │                  │
        │    Monitors &    │   Processes      │  Auto-Merge
        │    Auto-Fixes    │   AI Messages    │  Trusted PRs
        │                  │                  │
        └──────────────────┼──────────────────┘
                           │
                ┌──────────▼──────────┐
                │   Cron Scheduler    │
                │   (System Service)  │
                └──────────┬──────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────▼────────┐  ┌──────▼─────────┐  ┌────▼──────────┐
│    Trading     │  │     Social     │  │     Phase     │
│   Pipeline     │  │   Promotion    │  │  Progression  │
│   (Hourly)     │  │   (Every 4h)   │  │   (Daily)     │
└────────────────┘  └────────────────┘  └───────────────┘
```

**Key Features:** All autonomous agents run as services, Telegram is primary interface

---

## Component Details

### 1. Telegram Bot (Primary Interface)

**Purpose:** User's main control panel

**Functions:**
- Receive commands (`/status`, `/health`, `/metrics`, etc.)
- Send notifications (trades, alerts, reports)
- Approval workflow for risky changes
- Real-time system monitoring

**Status:** Code exists, not deployed
**File:** `scripts/telegram_command_bot.py`

### 2. Self-Healing Agent

**Purpose:** 24/7 system maintenance

**Auto-Fixes:**
- Git locks (`.git/index.lock`)
- Stale data files
- File permissions
- Disk space issues
- Hung processes
- Broken cron jobs

**Alerts User When:**
- Cannot auto-fix
- Critical issue detected
- Multiple failures

**Status:** Code exists, not running as service
**File:** `scripts/self_healing_agent.py`

### 3. Coordination Agent

**Purpose:** AI-to-AI task coordination

**Functions:**
- Reads `ai/coordination/messages.jsonl`
- Routes tasks to appropriate AI agent
- Updates `ai/coordination/status.json`
- Executes safe autonomous tasks
- Requests approval for risky tasks

**Agents Coordinated:**
- Copilot (GitHub PRs)
- Claude Code (CLI sessions)
- ChatGPT (analysis, research)
- Claude Web (web research)

**Status:** Code exists, not running as service
**File:** `scripts/coordination_agent.py`

### 4. Auto-Merge Workflow

**Purpose:** Merge PRs without user intervention

**Criteria:**
- From trusted sources (Copilot, etc.)
- All CI checks pass
- No merge conflicts
- Not draft PR
- Meets safety rules

**Status:** ✅ Active and working
**File:** `.github/workflows/auto-merge.yml`

### 5. Cron Jobs

**Purpose:** Scheduled autonomous operations

**Jobs:**
| Schedule | Task | Purpose |
|----------|------|---------|
| Hourly | Trading Pipeline | Execute trading strategy |
| Every 4h | Social Promotion | Post signals to social media |
| Every 15m | Health Check | System diagnostics |
| Daily 8am | Recalibration | Update models |
| Daily 8pm | Performance Report | Daily P&L summary |
| Every 5m | Coordination | Process AI messages |
| Daily Midnight | Phase Progression | Auto-scale deployment |

**Status:** Script exists to install, not deployed
**File:** `scripts/auto_setup_cron.py`

---

## Data Flow

### Autonomous Trading Cycle

```
1. Data Fetchers (Cron - Hourly)
   ↓
   Fetch Polymarket positions, prices, balances
   ↓
   Write to state/*.json

2. Alpha Model
   ↓
   Read state files
   ↓
   Calculate edge, confidence, fair price
   ↓
   Write to state/alpha_signals.json

3. Risk Engine
   ↓
   Read alpha signals + bankroll
   ↓
   Apply Kelly sizing + hard limits
   ↓
   Write to state/risk_assessment.json

4. Decider
   ↓
   Read risk assessment
   ↓
   Generate proposed actions
   ↓
   Write to state/planned_actions.json

5. Executor (DRYRUN)
   ↓
   Read planned actions
   ↓
   Validate safety gates
   ↓
   [DRYRUN] Log what would happen
   ↓
   Write to logs/executor_*.jsonl

6. Notification
   ↓
   Read executor output
   ↓
   Format Telegram message
   ↓
   Send to user for approval
```

### Self-Healing Cycle

```
Every 5 minutes:
   ↓
1. Check system health
   - Git locks
   - Stale data
   - Disk space
   - Process status
   - File permissions
   ↓
2. Detect issues
   ↓
3. Attempt auto-fix
   ↓
4. Log action
   ↓
5. If cannot fix: Alert user
   Otherwise: Continue silently
   ↓
6. Save state
   ↓
   [Sleep 5 minutes, repeat]
```

### AI Coordination Cycle

```
Every 5 minutes:
   ↓
1. Read ai/coordination/messages.jsonl
   ↓
2. Filter messages for this agent
   ↓
3. Process each message:
   - If safe task: Execute
   - If risky task: Request approval
   - If analysis: Generate response
   ↓
4. Write results to messages.jsonl
   ↓
5. Update ai/coordination/status.json
   ↓
   [Sleep 5 minutes, repeat]
```

---

## Service Dependencies

```
systemd services:
├── self-healing-agent.service
│   ├── Depends: network.target
│   └── Restarts: always (10s delay)
│
├── coordination-agent.service
│   ├── Depends: network.target
│   └── Restarts: always (10s delay)
│
└── hands-off-telegram.service
    ├── Depends: network.target
    ├── Requires: TELEGRAM_BOT_TOKEN
    └── Restarts: always (10s delay)

cron jobs:
├── trading_pipeline (hourly)
├── social_promotion (4h)
├── health_check (15m)
├── daily_recalibration (8am)
├── performance_report (8pm)
├── coordination_agent (5m) [redundant with service]
└── phase_progression (midnight)

GitHub Actions:
├── auto-merge.yml
│   ├── Triggers: PR events, check completions
│   └── Merges trusted PRs automatically
│
├── ai-intake.yml
│   ├── Triggers: Issue comments with /plan
│   └── Generates planning responses
│
└── agent-coordination-notify.yml
    ├── Triggers: Coordination file changes
    └── Notifies relevant agents
```

---

## Network Topology

```
Internet
   │
   ├─── GitHub (Source control + CI/CD)
   │    ├── Workflows run on GitHub servers
   │    ├── Auto-merge PRs
   │    └── Coordinate AI agents
   │
   ├─── Telegram (User interface)
   │    ├── Receives commands from user
   │    └── Sends notifications to user
   │
   ├─── Polymarket (Trading venue)
   │    ├── Fetch positions
   │    ├── Fetch prices
   │    └── [Future] Execute trades
   │
   └─── Social Media (Optional)
        ├── Twitter/X (signal posting)
        └── Reddit (signal posting)

Local System (Where services run)
   ├── systemd services (24/7)
   │   ├── self-healing-agent
   │   ├── coordination-agent
   │   └── telegram-bot
   │
   ├── cron jobs (scheduled)
   │   └── Various automated tasks
   │
   └── State files
       ├── state/*.json (system state)
       ├── logs/*.jsonl (audit trail)
       └── ai/coordination/*.jsonl (AI messages)
```

---

## File System Layout

```
/opt/hands-off-engine/  (or ~/hands-off-engine)
│
├── scripts/
│   ├── self_healing_agent.py          ← Service #1
│   ├── coordination_agent.py          ← Service #2
│   ├── telegram_command_bot.py        ← Service #3
│   └── autonomous_phase_manager.py    ← Cron job
│
├── .github/workflows/
│   ├── auto-merge.yml                 ← GitHub automation
│   ├── ai-intake.yml
│   └── agent-coordination-notify.yml
│
├── state/
│   ├── alpha_signals.json
│   ├── risk_assessment.json
│   ├── planned_actions.json
│   ├── self_healing_state.json
│   └── trading_mode.json
│
├── ai/coordination/
│   ├── messages.jsonl                 ← AI-to-AI messages
│   └── status.json                    ← Coordination state
│
├── logs/
│   ├── executor_*.jsonl
│   └── pipeline_*.log
│
└── /var/log/hands-off/               ← Service logs
    ├── self-healing.log
    ├── coordination.log
    └── telegram.log
```

---

## Interaction Patterns

### User → System

**Via Telegram (Target):**
```
User sends: /status
   ↓
Telegram bot receives command
   ↓
Reads state files
   ↓
Formats response
   ↓
Sends back to user
   [Total time: < 5 seconds]
```

**Via CLI (Current):**
```
User launches: claude code
   ↓
Claude reads state/docs
   ↓
User asks question
   ↓
Claude generates response
   [Total time: minutes]
```

### System → User

**Auto-notification:**
```
Trading pipeline completes
   ↓
Writes executor output
   ↓
Notification script reads output
   ↓
Formats Telegram message
   ↓
Sends to user
   [No user action needed]
```

**Alert:**
```
Self-healing detects unfixable issue
   ↓
Logs error
   ↓
Sends Telegram alert
   ↓
User receives notification
   ↓
User decides: fix via Telegram or launch CLI
```

### AI → AI

**Via coordination files:**
```
Copilot creates PR
   ↓
GitHub workflow triggers
   ↓
Writes message to ai/coordination/messages.jsonl
   ↓
Coordination agent reads file
   ↓
Routes to Claude Code
   ↓
Claude reads message
   ↓
Claude writes response
   ↓
Coordination agent processes response
   [All automated, no user involvement]
```

---

## Activation Sequence

**When following `AUTONOMOUS_ACTIVATION_RUNBOOK.md`:**

```
1. Prerequisites verified
   ↓
2. Install systemd services
   ├── self-healing-agent.service
   ├── coordination-agent.service
   └── hands-off-telegram.service
   ↓
3. Configure Telegram credentials
   ↓
4. Start all services
   ↓
5. Install cron jobs
   ↓
6. Test end-to-end
   ├── Send Telegram command
   ├── Simulate issue for self-healing
   └── Create coordination message
   ↓
7. Monitor 24h
   ↓
8. Update documentation
   ↓
9. System fully autonomous ✅
```

---

## Success Metrics

### Before Activation
- CLI usage: Daily
- User time: ~30 min/week
- Auto-fixes: None (manual)
- Telegram: Not connected
- Services: 0/3 running
- Autonomous: 30%

### After Activation
- CLI usage: < 1x/month
- User time: ~5 min/week
- Auto-fixes: Continuous
- Telegram: Primary interface
- Services: 3/3 running
- Autonomous: 99%

---

## Security Layers

```
Layer 1: DRYRUN Default
   ↓
   All trading operations default to DRYRUN
   LIVE mode requires explicit approval

Layer 2: Hard Limits
   ↓
   Max position: $50 (baby_mode)
   Max daily loss: $200
   Max open risk: $500

Layer 3: Safety Gates
   ↓
   Multiple validation checks before any action
   Circuit breakers on anomalies

Layer 4: Approval Workflow
   ↓
   Risky changes require user approval via Telegram
   Timeout if no response

Layer 5: Audit Trail
   ↓
   All actions logged to JSONL
   Immutable record for review
```

---

## Monitoring Points

**System Health:**
- Service uptime (systemd status)
- Log errors (grep logs)
- Disk space (df -h)
- Process count (ps aux)

**Trading Health:**
- Last pipeline run (state files)
- Current positions (API fetch)
- Balance changes (finance tracking)
- Error rate (executor logs)

**Autonomous Health:**
- Self-healing fix count
- Coordination message volume
- Telegram response time
- Cron job success rate

---

## Future Enhancements

**Phase 1 (Current):**
- ✅ GitHub auto-merge
- 🔄 Core services (to be activated)

**Phase 2:**
- Auto-approve small trades
- Dynamic risk adjustment
- Multi-strategy portfolio

**Phase 3:**
- Fully autonomous execution
- Self-optimizing models
- Cross-market arbitrage

**Phase 4:**
- Multi-venue trading
- Advanced ML models
- Minimal human oversight

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-01  
**Status:** Describes current + target state  
**Next:** Execute activation runbook
