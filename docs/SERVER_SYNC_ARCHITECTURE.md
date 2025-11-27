# Server-Repository Sync Architecture

**Status:** IMPLEMENTED  
**Last Updated:** 2025-11-27

## Overview

This document describes the automated bidirectional synchronization between the GitHub repository and the production server (DigitalOcean droplet). The goal is to minimize manual intervention - changes in the repo should automatically deploy to the server, and the system should operate autonomously.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         GITHUB                                   │
│  ┌─────────────┐    ┌────────────────┐    ┌─────────────────┐  │
│  │    Code     │    │ GitHub Actions │    │   Copilot /     │  │
│  │  (main)     │───>│ sync-to-server │    │   AI Agents     │  │
│  └─────────────┘    └───────┬────────┘    └─────────────────┘  │
│                             │                                    │
└─────────────────────────────│────────────────────────────────────┘
                              │ Telegram notification
                              │ "New commit pushed"
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PRODUCTION SERVER                            │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Server Sync Agent (systemd)                   │ │
│  │  • Checks GitHub every 5 minutes                           │ │
│  │  • Pulls new commits automatically                         │ │
│  │  • Restarts affected services                              │ │
│  │  • Sends Telegram notification on sync                     │ │
│  └───────────────────────────┬────────────────────────────────┘ │
│                              │                                   │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │Self-Healing │    │Coordination │    │  Telegram   │         │
│  │   Agent     │    │   Agent     │    │    Bot      │         │
│  └─────────────┘    └─────────────┘    └─────────────┘         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                   Trading Pipeline                         │ │
│  │           (cron - runs every hour)                         │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. GitHub Workflow: `sync-to-server.yml`

**Location:** `.github/workflows/sync-to-server.yml`

**Triggers:** Push to `main` branch

**Actions:**
1. Sends Telegram notification about new commit
2. Logs sync trigger info

**Note:** This workflow is informational - the actual sync is pull-based from the server for security.

### 2. Server Sync Agent

**Location:** `scripts/server_sync_agent.py`

**Runs as:** systemd service (`server-sync-agent.service`)

**Interval:** Every 5 minutes

**Actions:**
1. Fetches latest commits from `origin/main`
2. Compares local and remote commit SHAs
3. If different, pulls changes with rebase
4. Determines which services need restart based on changed files
5. Restarts affected services
6. Sends Telegram notification about successful sync

### 3. Systemd Services

All services are defined in `scripts/systemd/`:

| Service | Purpose | Restart on Code Change |
|---------|---------|----------------------|
| `server-sync-agent` | Pulls code, restarts services | Yes |
| `self-healing-agent` | Auto-fixes common issues | Yes |
| `coordination-agent` | AI-to-AI communication | Yes |
| `telegram-bot` | User commands via Telegram | Yes |

## Deployment

### Initial Setup (one-time)

On the server:

```bash
cd /root/hands-off-engine

# Install all services
sudo ./scripts/deploy_services.sh install

# Start all services
sudo ./scripts/deploy_services.sh start

# Check status
./scripts/deploy_services.sh status
```

### After This PR is Merged

Once this PR is merged to main, the server sync agent will:
1. Detect the new commit (within 5 minutes)
2. Pull the changes automatically
3. Install/update systemd service files
4. Restart relevant services
5. Notify you via Telegram

**No manual intervention required!**

## Monitoring

### Check Service Status

```bash
# Quick status
./scripts/deploy_services.sh status

# Detailed status
sudo systemctl status server-sync-agent
sudo systemctl status self-healing-agent
sudo systemctl status coordination-agent
sudo systemctl status telegram-bot
```

### View Logs

```bash
# Server sync agent
tail -f /var/log/server-sync-agent.log

# Self-healing agent
tail -f /var/log/self-healing-agent.log

# Coordination agent
tail -f /var/log/coordination-agent.log

# Telegram bot
tail -f /var/log/telegram-bot.log
```

### Sync State

```bash
# View sync state
cat state/server_sync_state.json
```

## Troubleshooting

### Sync Not Happening

1. Check if sync agent is running:
   ```bash
   sudo systemctl status server-sync-agent
   ```

2. Check logs for errors:
   ```bash
   tail -50 /var/log/server-sync-agent.log
   ```

3. Force a sync:
   ```bash
   sudo python3 scripts/server_sync_agent.py --once --force
   ```

### Service Won't Start

1. Check service file exists:
   ```bash
   ls -la /etc/systemd/system/server-sync-agent.service
   ```

2. Reinstall services:
   ```bash
   sudo ./scripts/deploy_services.sh install
   ```

3. Check systemd logs:
   ```bash
   sudo journalctl -u server-sync-agent -n 50
   ```

### Git Conflicts

The sync agent handles this automatically by:
1. Trying `git pull --rebase`
2. If that fails, aborting rebase and doing regular merge
3. If that fails, sending Telegram alert

To manually fix:
```bash
cd /root/hands-off-engine
git fetch origin main
git reset --hard origin/main
```

## Security

- **Pull-based sync:** Server pulls from GitHub (not push) to avoid exposing server to internet
- **No credentials on server:** Uses existing SSH key for git operations
- **Limited permissions:** Services run as root but with resource limits (CPU, memory)
- **Telegram for alerts:** Sensitive operations are notified, not automated

## Manual Override

If you need to make changes directly on the server:

1. Stop the sync agent:
   ```bash
   sudo systemctl stop server-sync-agent
   ```

2. Make your changes

3. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Server-side change: description"
   git push origin main
   ```

4. Restart sync agent:
   ```bash
   sudo systemctl start server-sync-agent
   ```

## Related Documentation

- `ai/DEPLOYMENT_STATUS.md` - Current deployment state
- `ai/DEPLOYMENT_ZERO_TOUCH.md` - Zero-touch architecture guide
- `docs/PRODUCTION_DEPLOYMENT.md` - General deployment guide
- `USER_INTERFACE.md` - Telegram interface for users
