# Deployment Configuration

This directory contains deployment configurations for the Hands-Off Engine autonomous trading system.

## Autonomous Trader

The `autonomous_trader.py` script runs continuously, executing the trading pipeline every 15 minutes.

### Option 1: systemd Service (Recommended)

The systemd service provides:
- Automatic startup on boot
- Auto-restart on failure
- Proper logging via journald
- Security hardening

#### Installation

1. Copy the service file:
```bash
sudo cp deploy/autonomous-trader.service /etc/systemd/system/
```

2. Create user and directories (if needed):
```bash
sudo useradd -r -s /bin/false hands-off
sudo mkdir -p /var/log
```

3. Configure environment variables:
```bash
sudo mkdir -p /etc/systemd/system/autonomous-trader.service.d/
sudo tee /etc/systemd/system/autonomous-trader.service.d/override.conf << EOF
[Service]
Environment="TELEGRAM_BOT_TOKEN=your-token-here"
Environment="TELEGRAM_CHAT_ID=your-chat-id-here"
EOF
```

4. Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable autonomous-trader
sudo systemctl start autonomous-trader
```

5. Check status:
```bash
sudo systemctl status autonomous-trader
sudo journalctl -u autonomous-trader -f
```

#### Management Commands

```bash
# Start/stop/restart
sudo systemctl start autonomous-trader
sudo systemctl stop autonomous-trader
sudo systemctl restart autonomous-trader

# View logs
sudo journalctl -u autonomous-trader -n 100
sudo journalctl -u autonomous-trader -f  # Follow logs

# Check health
curl http://localhost:8899/health
```

### Option 2: Cron (Alternative)

If systemd is not available, use cron to run the trader periodically.

See `autonomous-trader.cron` for configuration.

#### Installation

```bash
crontab -e
# Paste content from autonomous-trader.cron
```

## Health Check Endpoint

The autonomous trader exposes a health check endpoint:

```bash
curl http://localhost:8899/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-27T14:00:00Z",
  "running": true,
  "cycle_count": 42,
  "last_cycle": "2025-11-27T13:45:00Z",
  "consecutive_errors": 0,
  "mode": "DRYRUN"
}
```

## Monitoring

- **Trading logs**: `logs/trading.jsonl`
- **Audit logs**: `logs/audit/audit_*.jsonl`
- **systemd logs**: `journalctl -u autonomous-trader`

## Safety Notes

1. **DRYRUN is default** - No real trades are executed unless `--live` flag is used
2. **Max 10%** of bankroll per position
3. **70% confidence threshold** to execute
4. **$100 max** per position
5. **Telegram alerts** on significant events (>$10)
