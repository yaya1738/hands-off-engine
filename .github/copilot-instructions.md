# Copilot Instructions for Hands-Off Engine

## Required Reading (Before Any Work)

1. **state/knowledge.json** - Bootstrap instructions, required reading list, agent instruction files
2. **AI_POLICY.md** - Mandatory policy for all AI agents
3. **termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md** - Canonical status + roadmap
4. **docs/claude/USER_PROFILE.md** - Meta-aware principle, self-improvement loop, who we serve
5. **docs/claude/AI_COORDINATION_ARCHITECTURE.md** - Multi-agent coordination principles
6. **docs/DEVELOPMENT_STANDARDS.md** - How to build things properly (rules need enforcement, components need monitoring)
7. **ai/coordination/status.json** - Current tasks and agent coordination state

**Critical:**
- When changing agent coordination, update ALL files listed in `agent_instruction_files` in knowledge.json.
- When creating rules, add enforcement. When creating components, add monitoring.

## Project Context

This is the **Hands-Off Engine** - a personal "money + decisions" automation system:
- Multi-node: Termux phone, DigitalOcean droplet, GitHub repo
- Multi-agent: Copilot, Claude-Code, ChatGPT, Claude-Web coordinating autonomously
- Primary domain: Polymarket trading with strong risk controls
- Goal: Minimize human effort while maximizing safe, compounding edge

## Architecture

```
Data Fetchers → Alpha Model → Decider (Brain) → Executor (Body) → Audit Trail
                    ↓              ↓                  ↓
              state/polymarket-model.json    DRYRUN/LIVE orders
```

### Key Components
- `alpha/` - Edge estimation, fair price calculation
- `decider/` - Converts alpha signals to PlannedActions (Kelly-style sizing)
- `executor/` - Validates and executes with safety checks (DRYRUN enforced)
- `audit/` - JSON Lines logging for accountability
- `ai/` - AI coordination, intake handler, multi-agent messaging
- `ai_nexus/` - Multi-brain orchestration, cost tracking, self-financing

## Coding Standards

### Python
- Use type hints for all function signatures
- Dataclasses for structured data
- Graceful degradation (fallback to stderr if file writes fail)
- Atomic writes for state files (write to .tmp, then move)

### Safety First
- **DRYRUN is default** - Never enable LIVE trading without explicit user approval
- Max 10% bankroll per position
- Min 70% confidence threshold to execute
- $100 max per position

### File Formats
- State files: JSON in `state/`
- Logs: JSONL in `logs/` (daily rotation)
- Coordination: JSONL in `ai/coordination/`

## Communication Protocol

| Channel | Usage | Purpose |
|---------|-------|---------|
| Telegram | 99% | Primary for routine ops |
| GitHub Issues | ~1% | Strategic planning via `/plan` |
| CLI | <1% | Emergency only |

## Current Priorities (Tier 1 Roadmap)

1. ✅ AI Intake stable
2. ⚠️ Lock minimal risk model → Create `docs/RISK_MODEL_V1.md`
3. ⚠️ Define Decider V1 → Document decision rules
4. ✅ Harden DRYRUN/LIVE safety

## Coordination

Check `ai/coordination/status.json` for:
- Current tasks assigned to you
- Messages from other agents
- System phase and priorities

Post updates to `ai/coordination/messages.jsonl` for cross-agent communication.

## Autonomous Operations (Auto-Merge Enabled)

The system operates autonomously. Copilot PRs can be auto-merged when:
- All CI checks pass (tests, linting, type checks)
- No changes to critical files (see below)
- PR is labeled `copilot` or `auto-merge`

The `.github/workflows/auto-merge.yml` workflow handles this automatically.

## What Requires Human Approval

These actions ALWAYS require explicit human approval:
- Enabling LIVE trading (changing DRYRUN to LIVE)
- Security changes (API keys, auth, permissions)
- Capital allocation changes (bankroll %, position limits)
- Changes to critical files:
  - `.env*` files
  - `**/secrets/**`
  - `.github/workflows/auto-merge.yml` (the auto-merge workflow itself)
  - `executor/ho_executor.py` (live trade execution)
  - `state/risk_profile.json` (risk parameters)

## What Can Be Auto-Merged

These can be merged automatically when CI passes:
- Bug fixes
- Documentation updates
- Test additions
- Logging improvements
- Non-critical refactors
- Self-healing agent updates
- Alpha model improvements (with tests)