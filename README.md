# Hands-Off Engine

## Status & Roadmap

See `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
for the current status and next steps.

### For any AI / agent working on this repo

Before doing anything substantial, the AI/agent MUST:

1. Read `termux-hands-off/docs/HANDS_OFF_RESEARCH_REPORT_2025-11-20.md`
2. Follow the roadmap and constraints described there.

## Overview

This repository is the canonical codebase for my "Hands-Off" personal finance, trading,
and automation engine. It is designed to be driven primarily by AI coding agents
(LLMs) with minimal manual involvement.

High-level goals:
- Central, versioned home for all core engine code (Termux + DigitalOcean).
- Safe, auditable evolution of risk models, execution logic, and infra scripts.
- Multi-agent friendly: can be used by ChatGPT, Claude Code CLI, aider, quad, etc.

This repo is intentionally minimal at first; existing scripts will be migrated into a
clean structure step by step.

## Zero-Touch Operation

The system is designed for **zero-touch operation** via Telegram. No CLI needed for routine tasks.

### Telegram Bot

Control the entire system from your phone with the Telegram bot:

**Commands:**
- `/status` - System overview
- `/health` - Detailed health check
- `/markets` - Current market opportunities
- `/balance` - Portfolio status
- `/approve <id>` - Approve pending changes
- `/task <desc>` - Queue tasks for AI agents
- `/help` - See all commands

**Notifications:**
- Edge detection alerts (new opportunities)
- Daily morning briefings
- Error/warning notifications
- Trade execution confirmations

**Setup:** See [docs/TELEGRAM_SETUP.md](docs/TELEGRAM_SETUP.md) for complete setup guide (5 minutes).

**Quick Start:**
```bash
# 1. Get bot token from @BotFather on Telegram
# 2. Get your chat ID from @userinfobot
# 3. Set environment variables
export TELEGRAM_BOT_TOKEN="your_token_here"
export TELEGRAM_CHAT_ID="your_chat_id_here"

# 4. Install dependencies
pip3 install requests

# 5. Test the bot
python3 telegram/telegram_bot_listener.py --test

# 6. Run the bot
python3 telegram/telegram_bot_listener.py
```

For production deployment as a systemd service, see the full setup guide.