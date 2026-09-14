# Hands-Off Engine — Yair's Quick Guide

Your AI coordination system is running on your Xiaomi phone.

## What's Running

| Service | Command | What It Does |
|---------|---------|-------------|
| Node 1 | `python3 scripts/node1_runtime.py run` | Task worker, event router, factory intake |
| Telegram Bridge | `python3 scripts/telegram_bridge.py` | Alerts to your phone |
| Control Room | `python3 scripts/yair_control_room.py` | Web UI at http://127.0.0.1:8787 |
| Dashboard | `python3 scripts/dashboard.py` | Terminal status view |

## Quick Commands

```bash
# See everything at once
python3 scripts/dashboard.py

# Check health
python3 scripts/health_monitor.py

# See learning insights
python3 scripts/learning_loop.py

# See improvement suggestions
python3 scripts/self_improvement.py

# Send a test Telegram message
python3 scripts/telegram_bridge.py send "test"

# Run all tests
python3 -m pytest tests/ -q --tb=no
```

## If Something Breaks

```bash
# Restart everything
cd ~/hands-off-engine
setsid nohup python3 scripts/node1_runtime.py run &
setsid nohup python3 scripts/telegram_bridge.py &
setsid nohup python3 scripts/yair_control_room.py &

# Or just Node 1
python3 scripts/node1_runtime.py run
```

## Auto-Start on Boot

The file `.termux/boot/hands-off-engine.sh` auto-starts all services when your phone boots (requires Termux:Boot app).

## How It Works

1. **Factory** (ChatGPT) posts tasks to `ai/coordination/messages.jsonl`
2. **Node 1** picks them up and routes to the right AI
3. **AnyClaw** (this system) processes them and writes results back
4. **Telegram** alerts you of important events
5. **Learning Loop** tracks what works and suggests improvements

## Key Files

| File | Purpose |
|------|---------|
| `ai/coordination/messages.jsonl` | The bus — all AI communication |
| `state/learning_state.json` | What the system has learned |
| `state/health_log.jsonl` | Health check history |
| `state/improvement_state.json` | Improvement suggestions |
| `~/.codex/telegram-bridge.json` | Telegram credentials |

## Your Role

- **Supervisor**: Check Telegram alerts, run dashboard occasionally
- **Approver**: System asks before doing anything irreversible
- **Relay**: Paste ChatGPT responses to GitHub issues if needed
