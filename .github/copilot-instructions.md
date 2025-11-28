# Copilot Instructions for Hands-Off Engine

## Required Reading (Before Any Work)

1. **AI_POLICY.md** - Mandatory policy for all AI agents
2. **termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md** - Canonical status + roadmap
3. **state/knowledge.json** - Bootstrap instructions and primary docs
4. **ai/coordination/status.json** - Current tasks and agent coordination state

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

## Integration Patterns (CRITICAL - Read Before Building)

Before adding ANY external service integration:

1. **Search existing patterns first:**
   ```bash
   grep -r "SERVICE_NAME" --include="*.sh" --include="*.py" .
   ```

2. **Credential Storage Locations:**
   | Service | Variable | Location |
   |---------|----------|----------|
   | DigitalOcean | `DO_TOKEN` | `~/hands-off/state/do.env` |
   | Telegram | `TOKEN`, `CHAT_ID` | `state/tg/bots/handsoff.env` |
   | Exchanges | `OKX_API_KEY`, `KRAKEN_API_KEY` | `vault.json` |

3. **Match existing patterns exactly** - don't assume standard conventions

4. **Reference files:**
   - `termux-hands-off/agent/do_api.sh` - DigitalOcean pattern
   - `termux-hands-off/agent/agent.py` - Exchange API pattern
   - `termux-hands-off/agent/notify.py` - Telegram pattern

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

## What Requires Human Approval

- Merging PRs
- Enabling LIVE trading
- Strategic decisions
- Security changes
- Capital allocation changes