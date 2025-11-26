# Telegram Bot Setup Guide

Complete guide for setting up and configuring the Hands-Off Engine Telegram bot for zero-touch operation.

## Overview

The Telegram bot provides complete system control from your phone with no CLI needed. It includes:
- Command handlers for system monitoring and control
- Proactive notifications for important events
- Secure, user-restricted access
- Integration with audit system and state files

## Quick Start (5 Minutes)

### 1. Create Telegram Bot (2 minutes)

1. Open Telegram and search for `@BotFather`
2. Send: `/newbot`
3. Choose a name: `Hands Off Engine Bot` (or your preference)
4. Choose a username: `hands_off_bot` (must end in 'bot')
5. **Copy the token** - looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`

### 2. Get Your Chat ID (1 minute)

1. Search for `@userinfobot` on Telegram
2. Send it any message
3. **Copy your chat ID** - a number like `987654321`

### 3. Configure Environment (2 minutes)

```bash
# Set environment variables
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="987654321"

# Make permanent (add to ~/.bashrc)
echo 'export TELEGRAM_BOT_TOKEN="YOUR_TOKEN"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"' >> ~/.bashrc
source ~/.bashrc

# Or add to system environment
sudo tee -a /etc/environment <<EOF
TELEGRAM_BOT_TOKEN="YOUR_TOKEN"
TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
EOF
```

**Important**: Replace `YOUR_TOKEN` and `YOUR_CHAT_ID` with actual values.

### 4. Install Dependencies

```bash
# Install requests library for Telegram API
pip3 install requests

# Or use system package manager
sudo apt-get install python3-requests
```

### 5. Test the Bot

```bash
cd /path/to/hands-off-engine

# Test commands without Telegram connection
python3 telegram/telegram_bot_listener.py --test

# Test with actual Telegram connection
python3 telegram/telegram_bot_listener.py
```

Open Telegram and send `/status` to your bot. You should get a response!

Press `Ctrl+C` to stop the test.

## Available Commands

### Quick Status
- `/status` - System overview with health, latest execution, mode
- `/health` - Detailed health check of all components

### Trading Information
- `/markets` - Current market opportunities with edge estimates
- `/balance` - Portfolio/bankroll status and positions

### System Control
- `/approve <id>` - Approve pending system change
- `/reject <id>` - Reject pending system change
- `/task <description>` - Queue a task for autonomous agents

### AI Coordination
- `/agents` - View AI agent coordination status
- `/pending` - View pending approvals
- `/metrics` - Performance metrics (last 24 hours)

### Help
- `/help` - Show all available commands

## Notification System

The bot proactively sends notifications for important events:

### Edge Detection Alerts
When new market opportunities are detected with positive edge and high confidence, you'll receive an alert with:
- Market name
- Edge percentage
- Confidence level
- Quick link to see full details

### Daily Summary Reports
Every morning (default: 8 AM), receive a briefing with:
- System health status
- 24h performance metrics
- Current opportunities
- Action items requiring attention

### Error/Warning Notifications
Get immediately notified when:
- Data fetchers fail
- Health checks detect issues
- System components malfunction
- Self-healing attempts are made

### Trade Execution Confirmations
Receive confirmation when trades execute (DRYRUN or LIVE):
- Market and side
- Position size
- Price
- Expected edge
- Mode (DRYRUN/LIVE)

## Configuration

### Using Config File

Copy the example config and customize:

```bash
cp config/telegram_config.example.json config/telegram_config.json
```

Edit `config/telegram_config.json`:

```json
{
  "telegram": {
    "bot_token": "YOUR_BOT_TOKEN_HERE",
    "chat_id": "YOUR_CHAT_ID_HERE"
  },
  "notifications": {
    "edge_alerts": true,
    "daily_summary": true,
    "error_notifications": true,
    "trade_confirmations": true,
    "daily_summary_hour": 8
  },
  "commands": {
    "enabled": ["/status", "/health", "/markets", ...]
  },
  "security": {
    "restrict_to_chat_id": true,
    "require_approval_for_live_mode": true,
    "max_trade_size_usd": 100
  }
}
```

### Environment Variables

Required:
- `TELEGRAM_BOT_TOKEN` - Your bot token from @BotFather
- `TELEGRAM_CHAT_ID` - Your chat ID from @userinfobot

Optional:
- `TRADING_MODE` - Set to `DRYRUN` (default) or `LIVE`

### Notification Settings

Control notification behavior by editing the config file:

```json
{
  "notifications": {
    "edge_alerts": true,          // New opportunities
    "daily_summary": true,         // Morning briefing
    "error_notifications": true,   // System errors
    "trade_confirmations": true,   // Trade executions
    "daily_summary_hour": 8        // Hour for daily summary (0-23)
  }
}
```

## Deployment

### Option 1: Systemd Service (Recommended)

Run the bot 24/7 as a system service:

```bash
# Create service file
sudo tee /etc/systemd/system/telegram-bot.service <<EOF
[Unit]
Description=Hands-Off Engine Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/hands-off-engine
Environment="TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE"
Environment="TELEGRAM_CHAT_ID=YOUR_CHAT_ID_HERE"
ExecStart=/usr/bin/python3 /root/hands-off-engine/telegram/telegram_bot_listener.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/telegram-bot.log
StandardError=append:/var/log/telegram-bot.log

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Check status
sudo systemctl status telegram-bot

# View logs
sudo journalctl -u telegram-bot -f
# or
tail -f /var/log/telegram-bot.log
```

### Option 2: Screen/Tmux Session

For temporary deployment or testing:

```bash
# Using screen
screen -S telegram-bot
python3 telegram/telegram_bot_listener.py
# Press Ctrl+A then D to detach

# Reattach later
screen -r telegram-bot

# Using tmux
tmux new -s telegram-bot
python3 telegram/telegram_bot_listener.py
# Press Ctrl+B then D to detach

# Reattach later
tmux attach -t telegram-bot
```

### Option 3: Cron (Periodic Checks)

For notification-only setup without always-on bot:

```bash
# Edit crontab
crontab -e

# Add notification checks (every hour)
0 * * * * cd /root/hands-off-engine && python3 -c "from telegram.notifications import check_and_send_daily_summary; check_and_send_daily_summary()"
```

## Integration with Existing System

### Audit System Integration

Notifications automatically log to audit trail:

```python
from telegram.notifications import send_edge_alert

# Logged to state/notification_state.json
send_edge_alert(opportunities)
```

### State File Integration

Bot reads from existing state files:
- `state/polymarket-model.json` - Market data
- `state/performance_metrics.jsonl` - Metrics
- `state/approval_queue.json` - Pending approvals
- `state/knowledge.json` - System configuration
- `ai/coordination/status.json` - AI agent status

### AI Nexus Integration

For AI-powered responses (optional):

```python
# In bot_handlers.py
from ai_nexus import get_ai_summary

def cmd_status(self, args):
    # Use AI to generate intelligent summary
    summary = get_ai_summary(state_data)
    return summary
```

## Security Best Practices

### 1. Restrict Bot Access

**Always** set `TELEGRAM_CHAT_ID` to restrict bot to only your chat:

```bash
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
```

Without this, anyone who finds your bot can use it!

### 2. Keep Token Secret

Your bot token is like a password:
- Don't commit it to git
- Don't share it publicly
- Store in environment variables or secure config
- Regenerate if compromised (via @BotFather)

### 3. Use DRYRUN Mode

Default mode is DRYRUN (no real money):

```bash
export TRADING_MODE="DRYRUN"
```

Only enable LIVE mode after thorough testing:

```bash
export TRADING_MODE="LIVE"
```

### 4. Set Trade Limits

Configure maximum trade sizes in config:

```json
{
  "security": {
    "max_trade_size_usd": 100,
    "require_approval_for_live_mode": true
  }
}
```

### 5. Monitor Bot Activity

Check logs regularly:

```bash
# View recent activity
tail -100 /var/log/telegram-bot.log

# Watch in real-time
tail -f /var/log/telegram-bot.log

# Check systemd status
sudo systemctl status telegram-bot
```

## Troubleshooting

### Bot Doesn't Respond

**Symptoms**: Send `/status` but get no response

**Solutions**:
1. Check bot is running:
   ```bash
   sudo systemctl status telegram-bot
   # or
   ps aux | grep telegram_bot_listener
   ```

2. Verify environment variables:
   ```bash
   echo $TELEGRAM_BOT_TOKEN
   echo $TELEGRAM_CHAT_ID
   ```

3. Check logs for errors:
   ```bash
   tail -50 /var/log/telegram-bot.log
   ```

4. Test token manually:
   ```bash
   curl "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/getMe"
   ```

### "Unauthorized" Error

**Symptoms**: Bot logs show "Unauthorized" or 401 errors

**Solutions**:
1. Verify token is correct (check for typos)
2. Token may have expired - create new bot with @BotFather
3. Check for extra spaces in token

### Bot Responds to Wrong Person

**Symptoms**: Bot responds to other users, not just you

**Solutions**:
1. Set `TELEGRAM_CHAT_ID` environment variable
2. Verify chat ID is correct
3. Restart bot after setting chat ID

### Commands Not Working

**Symptoms**: `/status` returns "Unknown command"

**Solutions**:
1. Check command spelling (case-sensitive)
2. Verify commands are enabled in config
3. Check bot code has command handlers
4. Restart bot to reload code

### Notifications Not Sending

**Symptoms**: Expected notifications don't arrive

**Solutions**:
1. Check notification settings in config
2. Verify `TELEGRAM_CHAT_ID` is set
3. Check bot has permission to send messages
4. Review notification state file:
   ```bash
   cat state/notification_state.json
   ```

### State Files Missing

**Symptoms**: Commands return "No data available"

**Solutions**:
1. Run data fetchers to populate state files
2. Check state directory exists and is writable:
   ```bash
   ls -la state/
   ```
3. Verify file paths in code match actual structure

### Permission Errors

**Symptoms**: "Permission denied" when writing logs

**Solutions**:
1. Check log directory permissions:
   ```bash
   sudo mkdir -p /var/log
   sudo chmod 755 /var/log
   ```

2. Or change log path in code to user directory:
   ```python
   LOG_FILE = Path.home() / "telegram-bot.log"
   ```

## Testing

### Test Commands Locally

Without Telegram connection:

```bash
python3 telegram/telegram_bot_listener.py --test
```

This simulates commands and shows responses.

### Test Specific Handler

```python
# Test in Python REPL
from telegram.bot_handlers import BotHandlers

handlers = BotHandlers()
response = handlers.handle_command("/status")
print(response)
```

### Test Notifications

```python
# Test notification system
from telegram.notifications import NotificationSystem

notifier = NotificationSystem()

# Test edge alert
notifier.send_edge_alert([
    {'market': 'Test Market', 'edge': 0.08, 'confidence': 0.85}
])

# Test error notification
notifier.send_error_notification(
    'test_error',
    'This is a test error message'
)
```

### Integration Testing

```bash
# 1. Start bot in test mode
python3 telegram/telegram_bot_listener.py

# 2. In Telegram, send commands:
/status
/health
/markets
/balance
/help

# 3. Verify responses are correct

# 4. Check logs
cat /var/log/telegram-bot.log
```

## Advanced Usage

### Custom Commands

Add new commands by editing `telegram/bot_handlers.py`:

```python
class BotHandlers:
    def __init__(self):
        self.handlers = {
            # ... existing commands
            '/custom': self.cmd_custom,
        }
    
    def cmd_custom(self, args: List[str]) -> str:
        """Your custom command."""
        return "Custom response"
```

### AI-Powered Responses

Integrate with AI Nexus for intelligent responses:

```python
from ai_nexus import query_ai

def cmd_analyze(self, args: List[str]) -> str:
    """AI-powered market analysis."""
    query = " ".join(args)
    response = query_ai(f"Analyze: {query}")
    return response
```

### Scheduled Notifications

Set up cron jobs for periodic notifications:

```bash
# Edit crontab
crontab -e

# Daily summary at 8 AM
0 8 * * * cd /root/hands-off-engine && python3 -c "from telegram.notifications import send_daily_summary; send_daily_summary()"

# Check for new opportunities every 30 minutes
*/30 * * * * cd /root/hands-off-engine && python3 scripts/check_opportunities.py
```

### Multi-User Support

To support multiple users, modify the bot to accept multiple chat IDs:

```python
# In telegram_bot_listener.py
ALLOWED_CHAT_IDS = os.getenv("TELEGRAM_CHAT_IDS", "").split(",")

def process_update(self, update):
    chat_id = str(update.get("message", {}).get("chat", {}).get("id"))
    
    if chat_id not in ALLOWED_CHAT_IDS:
        logger.warning(f"Unauthorized chat: {chat_id}")
        return
    # ... rest of processing
```

## Monitoring and Maintenance

### Health Checks

Periodically verify bot health:

```bash
# Check bot is running
systemctl is-active telegram-bot

# Check last activity
tail -1 /var/log/telegram-bot.log

# Test bot responds
# Send /status in Telegram and verify response
```

### Log Rotation

Set up log rotation to prevent disk space issues:

```bash
# Create logrotate config
sudo tee /etc/logrotate.d/telegram-bot <<EOF
/var/log/telegram-bot.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

### Performance Monitoring

Monitor bot performance:

```bash
# Check memory usage
ps aux | grep telegram_bot_listener

# Check CPU usage
top -p $(pgrep -f telegram_bot_listener)

# Check response times
# Send /status and time the response
```

### Updates and Upgrades

When updating bot code:

```bash
# Pull latest changes
cd /root/hands-off-engine
git pull

# Restart bot
sudo systemctl restart telegram-bot

# Verify it's working
sudo systemctl status telegram-bot
```

## FAQ

### Q: Can I use the bot on multiple devices?

A: Yes! Telegram syncs across devices. Send commands from any device where you're logged in.

### Q: What if I lose my phone?

A: Log in to Telegram on another device using your phone number. The bot will work immediately.

### Q: Can I have multiple bots?

A: Yes, create multiple bots with @BotFather. Each needs its own token.

### Q: How much does it cost?

A: Telegram bots are free! No API costs, no message limits.

### Q: Is it secure?

A: Yes, when configured properly:
- Set `TELEGRAM_CHAT_ID` to restrict access
- Keep bot token secret
- Use HTTPS (Telegram API is HTTPS by default)
- Don't share sensitive data in messages

### Q: Can the bot make trades automatically?

A: Only if you enable LIVE mode and approve specific actions. Default is DRYRUN (no real money).

### Q: What if Telegram is down?

A: The bot will queue messages and retry. Check logs for system status.

### Q: Can I run multiple bots?

A: Yes, but they need different tokens. Useful for separating dev/prod environments.

## Support and Resources

- **Telegram Bot API**: https://core.telegram.org/bots/api
- **BotFather Guide**: https://core.telegram.org/bots#botfather
- **Repository Issues**: https://github.com/yaya1738/hands-off-engine/issues

## Summary

You now have a complete Telegram bot setup for zero-touch system operation:

✅ Command handlers for system control
✅ Proactive notifications for important events  
✅ Secure, restricted access
✅ Integration with existing system
✅ 24/7 operation via systemd

**Next Steps**:
1. Test all commands
2. Verify notifications work
3. Deploy as systemd service
4. Monitor for 24h to ensure stability
5. Enjoy zero-touch operation! 🚀
