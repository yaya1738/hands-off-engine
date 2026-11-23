# Telegram Bot Setup - 5 Minute Guide

**Result:** Control entire system from your phone. Zero CLI needed.

---

## Step 1: Create Bot (2 minutes)

1. Open Telegram app
2. Search for `@BotFather`
3. Send: `/newbot`
4. Choose name: "Hands Off Engine Bot" (or whatever you want)
5. Choose username: `hands_off_bot` (or whatever - must end in 'bot')
6. **Copy the token** BotFather gives you (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

---

## Step 2: Get Your Chat ID (1 minute)

1. Search for `@userinfobot` on Telegram
2. Send any message to it
3. **Copy your chat ID** (it's a number like `987654321`)

---

## Step 3: Configure Server (2 minutes)

```bash
# Set environment variables (replace with your values)
export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_ID="987654321"
# Only needed when using a group chat: authorize one specific sender ID.
# Private chats are authorized only when chat ID and sender ID are the same.
# export TELEGRAM_USER_ID="987654321"

# Make permanent (add to ~/.bashrc or /etc/environment)
echo 'export TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"' >> ~/.bashrc
echo 'export TELEGRAM_CHAT_ID="987654321"' >> ~/.bashrc

# Or add to system environment
sudo tee -a /etc/environment <<EOF
TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
TELEGRAM_CHAT_ID="987654321"
EOF
```

---

## Step 4: Install Dependencies

```bash
# Install requests library
pip3 install requests

# Or if that fails:
sudo apt-get install python3-requests
```

---

## Step 5: Test It

```bash
cd /root/hands-off-engine

# Test without Telegram (verify commands work)
python3 telegram/telegram_bot_listener.py --test

# Test with Telegram (verify connection)
python3 telegram/telegram_bot_listener.py
```

**Then open Telegram and send:**
- `/status`
- `/help`

You should get responses!

Press Ctrl+C to stop the test.

---

## Step 6: Deploy as Service (Optional)

Make it run 24/7:

```bash
# Create systemd service
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

[Install]
WantedBy=multi-user.target
EOF

# Replace YOUR_TOKEN_HERE and YOUR_CHAT_ID_HERE with actual values

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

# Check status
sudo systemctl status telegram-bot
tail -f /var/log/telegram-bot.log
```

---

## Available Commands

Once running, send these from Telegram:

- `/status` - Full system status
- `/metrics` - Performance metrics (24h)
- `/health` - Run health check
- `/agents` - AI coordination status
- `/approve <id>` - Approve pending change
- `/reject <id>` - Reject pending change
- `/help` - Command list

---

## Verify It's Working

1. Send `/status` from Telegram
2. You should get system status back
3. Send `/health`
4. You should get health check results

**If it works: You never need CLI again for routine ops!**

---

## Troubleshooting

**Bot doesn't respond:**
- Check environment variables are set
- Check bot is running: `sudo systemctl status telegram-bot`
- Check logs: `tail -f /var/log/telegram-bot.log`
- Verify token is correct (ask @BotFather if unsure)

**"Unauthorized" error:**
- Wrong token - check value
- Token expired - create new bot with @BotFather

**Bot responds to wrong person:**
- TELEGRAM_CHAT_ID is mandatory; the listener refuses to poll without it.
- For a group chat, also set TELEGRAM_USER_ID to the one authorized sender.

---

## Security Notes

- Bot token is like a password - keep it secret.
- The listener fails closed if TELEGRAM_CHAT_ID is missing.
- Private chats require the configured chat ID to equal the sender's Telegram user ID.
- Group chats require both the configured group chat ID and an explicit TELEGRAM_USER_ID.
- Other members of an allowlisted group cannot issue commands.
- The primary bridge also checks chatIds and, for groups, userIds from ~/.codex/telegram-bridge.json.

---

**Setup time:** ~5 minutes
**Result:** Complete system control from your phone, zero CLI needed
