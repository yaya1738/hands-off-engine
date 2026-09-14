# Hands-Off Engine

Multi-AI coordination system running on Android phone (Termux/proot).

## Architecture

```
Factory (ChatGPT) → messages.jsonl → AnyClaw (this) → task_result → Factory
                        ↕
                   Telegram alerts → Yair
                   Control Room → browser
                   Learning Loop → self-improvement
```

## Quick Start

```bash
# Start everything
setsid nohup python3 scripts/node1_runtime.py run &
setsid nohup python3 scripts/telegram_bridge.py &
setsid nohup python3 scripts/yair_control_room.py &
setsid nohup python3 scripts/scheduler.py &

# Dashboard
python3 scripts/dashboard.py
```

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/node1_runtime.py` | Unified compute node |
| `scripts/telegram_bridge.py` | Telegram alerts |
| `scripts/yair_control_room.py` | Web UI (localhost:8787) |
| `scripts/dashboard.py` | Terminal dashboard |
| `scripts/learning_loop.py` | Task outcome tracking |
| `scripts/health_monitor.py` | Service health checks |
| `scripts/self_improvement.py` | Improvement generator |
| `scripts/state_integrity.py` | State file tamper detection |
| `scripts/bus_cleanup.py` | Archive old bus messages |
| `scripts/scheduler.py` | Periodic improvement cycles |
| `scripts/improvement_cycle.py` | All subsystems in one cycle |
| `scripts/web_research.py` | Public data research |

## Coordination Bus

`ai/coordination/messages.jsonl` — canonical transport for all AI communication.

Parties: operator, factory, anyclaw, chatgpt, grok, openclaw, claude-code, copilot, telegram, system_internal

## Security

- Fail-closed authority: `execution_enabled` always False
- Sender validation: unknown parties rejected from bus
- State integrity: SHA-256 checksums for critical files
- No secrets in bus, no live execution without approval

## Tests

```bash
python3 -m pytest tests/ -q --tb=no
```
