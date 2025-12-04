# Messaging Integration - Quick Start

## Telegram Setup (5 minutes)

1. **Create Bot:**
   - Open Telegram
   - Search: `@BotFather`
   - Send: `/newbot`
   - Name it: "Hands-Off System"
   - Username: `handsoff_yair_bot` (or similar)
   - **Copy the token**

2. **Get Chat ID:**
   - Search: `@userinfobot`
   - Send: `/start`
   - **Copy your ID**

3. **Activate:**
   ```bash
   ./scripts/setup_telegram.sh YOUR_BOT_TOKEN YOUR_CHAT_ID
   ```

4. **Start your bot:**
   - Search for your bot in Telegram
   - Send: `/start`

Done! You'll receive notifications automatically.

---

## Commands

Send these to your bot:
- `/status` - System overview
- `/trades` - Recent trades
- `/bounties` - Bounty status
- `/balance` - Account balances
- `/logs` - Recent activity

---

## WhatsApp Setup (Optional, 10 minutes)

Only needed for critical alerts.

1. **Twilio Account:**
   - https://www.twilio.com/try-twilio
   - Sign up, verify phone
   - Get Account SID & Auth Token

2. **Configure:**
   ```bash
   nano .env.handsoff_whatsapp
   # Add credentials
   ```

3. **Activate Sandbox:**
   - https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
   - Send "join xxx" to Twilio's WhatsApp number

4. **Test:**
   ```bash
   python3 autonomous/whatsapp_notifier.py --test
   ```

---

## What You Get

**Telegram (Recommended):**
- Trading wins/losses
- Bounty updates
- System health
- Interactive commands
- Free forever

**WhatsApp (Optional):**
- Critical alerts only
- PR merged notifications
- System failures
- $15 free trial

---

## Monitoring

```bash
# Check bridge status
tail -f logs/messaging_bridge.log

# Check stats
cat state/messaging_bridge.json

# Restart if needed
pkill -f messaging_bridge
nohup python3 autonomous/messaging_bridge.py --continuous > logs/messaging_bridge.log 2>&1 &
```

---

## Troubleshooting

**No messages arriving:**
```bash
# Test Telegram
python3 autonomous/telegram_notifier.py --test

# Check credentials
cat .env.handsoff_telegram

# Verify bot started (send /start in Telegram)
```

**Commands not working:**
- Make sure you sent `/start` to your bot first
- Check bridge is running: `ps aux | grep messaging_bridge`
- Check logs: `tail -f logs/messaging_bridge.log`

---

**Full docs:** `docs/MESSAGING_SETUP.md`
