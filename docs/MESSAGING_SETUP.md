== Telegram & WhatsApp System Integration

Get real-time notifications about trading, bounties, and system health directly to your phone.

---

## What You'll Get:

✅ **Telegram Bot:**
- Real-time trading notifications
- Bounty status updates
- System health alerts
- Interactive commands (/status, /trades, /bounties)
- Lightweight, instant delivery

✅ **WhatsApp Notifications:**
- Critical alerts only
- High-priority system issues
- Bounty merged/paid notifications
- Familiar interface

✅ **Unified Bridge:**
- Routes messages to appropriate channel
- Critical → WhatsApp
- Regular → Telegram
- Monitors all system events
- Single notification system

---

## Setup Option 1: Telegram Only (5 minutes, recommended)

### Step 1: Create Bot

1. Open Telegram on your phone
2. Search for `@BotFather`
3. Send: `/newbot`
4. Name your bot: "Hands-Off System" (or anything)
5. Choose username: ending in "bot" (e.g., `handsoff_yair_bot`)
6. **Copy the bot token** (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Step 2: Get Your Chat ID

1. Search for `@userinfobot` in Telegram
2. Send: `/start`
3. **Copy your ID** (looks like: `123456789`)

### Step 3: Configure

```bash
cd /root/hands-off-engine
nano .env.handsoff_telegram
```

Paste your credentials:
```bash
TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
TELEGRAM_CHAT_ID="123456789"
```

Save (Ctrl+X, Y, Enter)

### Step 4: Start Your Bot

1. Search for your bot in Telegram (the username you created)
2. Send: `/start`
3. You'll see a welcome message

### Step 5: Test

```bash
python3 autonomous/telegram_notifier.py --test
```

You should receive: "🤖 Telegram notifier test successful!"

### Step 6: Activate Continuous Monitoring

```bash
nohup python3 autonomous/messaging_bridge.py --continuous > logs/messaging_bridge.log 2>&1 &
```

Done! You'll now receive:
- Trading wins/losses
- Bounty updates (PR merged, approved, paid)
- System alerts (process down, errors)
- Every 5 minutes, system checks for new events

---

## Setup Option 2: WhatsApp (10 minutes, optional)

WhatsApp is optional and best for critical alerts only.

### Step 1: Create Twilio Account

1. Visit: https://www.twilio.com/try-twilio
2. Sign up (free trial)
3. Verify your phone number
4. You get $15 credit (≈500 WhatsApp messages free)

### Step 2: Get Credentials

1. Go to: https://console.twilio.com
2. Copy **Account SID**
3. Click "Show" and copy **Auth Token**

### Step 3: Configure

```bash
nano .env.handsoff_whatsapp
```

Paste:
```bash
WHATSAPP_PHONE="+1234567890"  # Your phone with country code
TWILIO_ACCOUNT_SID="your-sid-here"
TWILIO_AUTH_TOKEN="your-token-here"
TWILIO_WHATSAPP_NUMBER="+14155238886"  # Twilio's WhatsApp sandbox
```

### Step 4: Activate WhatsApp Sandbox

1. Go to: https://console.twilio.com/us1/develop/sms/try-it-out/whatsapp-learn
2. You'll see a code like: "join happy-dog"
3. Send that message to `+1 415 523 8886` on WhatsApp
4. You'll receive confirmation

### Step 5: Test

```bash
python3 autonomous/whatsapp_notifier.py --test
```

You should receive: "🤖 WhatsApp notifier test successful!"

---

## Setup Option 3: Both (Best)

1. Complete Telegram setup above
2. Complete WhatsApp setup above
3. Start unified bridge:

```bash
nohup python3 autonomous/messaging_bridge.py --continuous > logs/messaging_bridge.log 2>&1 &
```

The system will automatically route:
- **Critical alerts → WhatsApp** (PR merged, system down)
- **Regular updates → Telegram** (trades, status, logs)
- **Commands → Telegram** (/status, /trades, etc.)

---

## Commands (Telegram Only)

Once your bot is running, send these commands:

- `/start` - Welcome message
- `/status` - System overview
- `/trades` - Recent trading activity
- `/bounties` - Bounty PR status
- `/balance` - Current balances
- `/logs` - Recent system activity

---

## What You'll Receive Automatically:

### Trading Notifications:
```
💰 Trade Executed

Action: BUY
Market: BTC $150k by Dec 2025
Amount: $25.00
Outcome: YES

Time: 21:30 UTC
```

### Bounty Notifications:
```
🎉 Bounty Update

PR #239: MERGED

$125 bounty is now claimable!

Time: 14:15 UTC
```

### System Alerts:
```
⚠️ System Alert

Component: Money Printer
Status: STOPPED

Check logs immediately!

Time: 03:45 UTC
```

---

## Monitoring

Check bridge status:
```bash
# Live log
tail -f logs/messaging_bridge.log

# Stats
cat state/messaging_bridge.json

# Process
ps aux | grep messaging_bridge
```

---

## Troubleshooting

### Telegram not sending:
```bash
# Test connection
python3 autonomous/telegram_notifier.py --test

# Check credentials
cat .env.handsoff_telegram

# Verify bot is started (send /start to your bot)
```

### WhatsApp not sending:
```bash
# Test connection
python3 autonomous/whatsapp_notifier.py --test

# Check credentials
cat .env.handsoff_whatsapp

# Verify sandbox is activated (send "join xxx" message)
```

### No notifications arriving:
```bash
# Check bridge is running
ps aux | grep messaging_bridge

# Check logs
tail -50 logs/messaging_bridge.log

# Restart bridge
pkill -f messaging_bridge
nohup python3 autonomous/messaging_bridge.py --continuous > logs/messaging_bridge.log 2>&1 &
```

---

## Cost

**Telegram:**
- Free forever
- Unlimited messages
- No API fees
- Recommended for main notifications

**WhatsApp (Twilio):**
- Free trial: $15 credit (≈500 messages)
- After trial: $0.005 per message
- For critical alerts only
- Optional

**WhatsApp (Alternative - whatsapp-web.js):**
- Free forever
- Uses your WhatsApp Web session
- More setup, less reliable
- Not recommended for production

---

## Security

✅ Bot tokens stored in `.env` files (not in git)
✅ Only sends to YOUR chat ID
✅ No incoming message processing (commands only)
✅ Twilio credentials secured

---

## Next Steps

1. **Minimum:** Setup Telegram (5 minutes)
   - Instant notifications
   - Interactive commands
   - Free forever

2. **Optional:** Add WhatsApp (10 minutes)
   - Critical alerts only
   - More familiar interface
   - $15 free trial

3. **Activate:** Start messaging bridge
   - Monitors all systems
   - Routes messages intelligently
   - Set and forget

---

**You'll never miss important updates again.**

Your phone becomes your system dashboard.

Setup Telegram now: Search @BotFather in Telegram and send `/newbot`
