# GitHub Automations - Hands-Off Engine

This document describes all GitHub Actions workflows in the repository and how they work together to minimize user effort.

## Automation Philosophy

The goal is **maximum autonomy with minimal user intervention**. Users should:
- Receive only essential notifications (via Telegram)
- Have issues and PRs auto-triaged
- See consolidated weekly updates instead of noise
- Only intervene when truly necessary

## Workflow Overview

| Workflow | Trigger | Purpose | User Effort Required |
|----------|---------|---------|---------------------|
| `issue-auto-assign.yml` | New issue | Auto-assigns to Copilot, adds labels | None |
| `ai-intake.yml` | `/plan` command | Processes planning requests | Issue creation only |
| `auto-merge.yml` | PR ready | Auto-merges safe PRs | None for safe PRs |
| `pr-sync.yml` | Push/schedule | Syncs PR branches, labels PRs | None |
| `weekly-digest.yml` | Weekly/manual | Consolidated status report | ~2 min review |
| `workflow-failure-notify.yml` | Workflow fails | Telegram alert | Only if action needed |
| `agent-coordination-notify.yml` | Coordination updates | Notifies agents | None |
| `tests.yml` | PR/push | Runs test suite | None |
| `ci.yml` | PR/push | Basic CI checks | None |

---

## Detailed Workflow Descriptions

### 1. Issue Auto-Assignment (`issue-auto-assign.yml`)

**Trigger:** When any new issue is opened

**What it does:**
1. Adds relevant labels based on title/body keywords:
   - `bug` for bug reports
   - `enhancement` for feature requests  
   - `documentation` for docs changes
   - `priority:high` for urgent issues
   - `copilot-assigned` for tracking
2. Posts acknowledgment comment
3. Notifies that Copilot will triage

**User effort:** Zero - just open the issue

---

### 2. AI Intake (`ai-intake.yml`)

**Trigger:** Comment containing `/plan` on issues

**What it does:**
1. Uses OpenAI to analyze the planning request
2. Generates implementation plan
3. Posts plan as issue comment
4. Enables handoff to Copilot for execution

**User effort:** Type `/plan <description>` on any issue

**Required secrets:**
- `OPENAI_API_KEY`

---

### 3. Auto-Merge (`auto-merge.yml`)

**Trigger:** PR review submitted or checks complete

**What it does:**
1. Checks if PR is from trusted author (Copilot, dependabot)
2. Verifies all checks pass
3. Validates changes are in safe paths (docs, tests)
4. Auto-merges if all criteria met
5. Posts notification if merge fails

**User effort:** None for safe PRs; manual review for risky changes

**Safe file patterns:**
- `docs/`
- `tests/`
- `*.md`
- `logs/`
- `.github/copilot-instructions.md`

**Risky file patterns (require review):**
- `executor/`
- `alpha/`
- `decider/`
- `config*`
- `*.env`
- `requirements.txt`
- `package.json`

---

### 4. PR Sync and Management (`pr-sync.yml`)

**Trigger:** 
- Push to main/master
- PR opened/updated
- Daily at 6 AM UTC

**What it does:**
1. Updates PR branches when base changes
2. Auto-labels PRs based on changed files:
   - `documentation` - docs/ or .md files
   - `testing` - tests/ or test_ files
   - `ai-coordination` - ai/ directory
   - `automation` - scripts/ directory
   - `ci-cd` - .github/ directory
   - `trading-core` + `needs-review` - executor/, alpha/, decider/
   - `configuration` + `needs-review` - config files
3. Marks stale PRs (7+ days inactive)

**User effort:** None

---

### 5. Weekly Digest (`weekly-digest.yml`)

**Trigger:** 
- Every Monday at 8 AM UTC
- Manual dispatch

**What it does:**
1. Generates comprehensive weekly report:
   - PRs merged/open
   - New/open issues
   - Commit count
   - CI success/failure rate
2. Sends Telegram notification with summary
3. Logs to coordination system

**User effort:** ~2 minutes to review weekly

**Required secrets:**
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

---

### 6. Workflow Failure Notification (`workflow-failure-notify.yml`)

**Trigger:** Any monitored workflow completes with failure

**Monitored workflows:**
- CI
- Tests
- AI Intake
- Auto-merge PRs
- PR Sync and Management

**What it does:**
1. Detects failed jobs
2. Sends immediate Telegram alert with:
   - Workflow name
   - Branch
   - Failed jobs
   - Link to run
3. Logs to coordination

**User effort:** Only if intervention needed

**Required secrets:**
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

---

### 7. Agent Coordination Notify (`agent-coordination-notify.yml`)

**Trigger:** Changes to coordination files:
- `ai/coordination/messages.jsonl`
- `ai/coordination/status.json`

**What it does:**
1. Checks for urgent coordination messages
2. Creates/updates coordination issue
3. Triggers Copilot via repository dispatch

**User effort:** None (agent-to-agent)

---

## Required Secrets

| Secret | Purpose | Required For |
|--------|---------|--------------|
| `OPENAI_API_KEY` | AI Intake processing | ai-intake.yml |
| `TELEGRAM_BOT_TOKEN` | Telegram notifications | weekly-digest, failure-notify |
| `TELEGRAM_CHAT_ID` | Telegram chat target | weekly-digest, failure-notify |
| `GITHUB_TOKEN` | Auto-provided | All workflows |

---

## User Notification Flow

```
GitHub Events
     │
     ▼
┌─────────────────┐
│  GitHub Actions │
│    Workflows    │
└────────┬────────┘
         │
         ▼
    ┌─────────┐     Critical alerts
    │ Filter  │────────────────────▶ 📱 Telegram
    └────┬────┘                      (immediate)
         │
         │ Weekly digest
         └────────────────────────▶ 📱 Telegram
                                     (Monday 8 AM)
```

---

## Adding New Workflows

When adding new workflows, follow these principles:

1. **Minimize user effort** - Automate as much as possible
2. **Use Telegram for alerts** - Not GitHub notifications
3. **Log to coordination** - Enable agent awareness
4. **Label appropriately** - For auto-merge classification
5. **Handle failures gracefully** - Don't break silently

---

## Maintenance

### Checking Workflow Health

```bash
# View recent workflow runs
gh run list --repo yaya1738/hands-off-engine --limit 10

# Check for failures
gh run list --repo yaya1738/hands-off-engine --status failure
```

### Manually Triggering Workflows

```bash
# Trigger weekly digest
gh workflow run weekly-digest.yml

# Trigger with inputs
gh workflow run weekly-digest.yml -f send_telegram=false
```

---

*Last updated: 2025-11-27*
*Part of the Hands-Off Engine autonomous system*
