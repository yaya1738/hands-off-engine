# Telegram Bot Setup - Super Simple Guide

**Time needed:** 5 minutes
**What you get:** Control everything from your phone

---

## Automatic Setup (Easiest)

Just run this command and follow the prompts:

```bash
cd /root/hands-off-engine
./scripts/setup_telegram.sh
```

The script will:
1. Guide you through creating the bot
2. Ask for your tokens
3. Save everything automatically
4. Test the connection
5. Send you a test message

**That's it!** Follow the on-screen instructions.

---

## Manual Setup (If you prefer)

### Step 1: Create Bot (2 min)

**On your phone, open Telegram:**

1. Search: `@BotFather`
2. Send: `/newbot`
3. Name: `Hands Off Engine Bot`
4. Username: `yourname_handsoff_bot` (or anything ending in `_bot`)
5. **Copy the token** BotFather gives you (looks like: `1234567890:ABCdef...`)

### Step 2: Get Your Chat ID (1 min)

**Still in Telegram:**

1. Search: `@userinfobot`
2. Send: `hi` (any message)
3. **Copy your ID** (the number it shows)

### Step 3: Save Tokens (30 sec)

**On your server:**

```bash
cd /root/hands-off-engine

# Paste your actual tokens here
export TELEGRAM_BOT_TOKEN="YOUR_TOKEN_HERE"
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID_HERE"

# Make permanent
echo "export TELEGRAM_BOT_TOKEN=\"YOUR_TOKEN_HERE\"" >> ~/.bashrc
echo "export TELEGRAM_CHAT_ID=\"YOUR_CHAT_ID_HERE\"" >> ~/.bashrc
```

### Step 4: Test (30 sec)

```bash
python3 telegram/telegram_command_bot.py << 'EOF'
from telegram.telegram_command_bot import TelegramCommandBot
bot = TelegramCommandBot()
print(bot.process_command("/status"))
EOF
```

**Check your Telegram** - you should see a message from your bot!

---

## After Setup

### Commands You Can Use

Send these to your bot in Telegram:

| Command | What it does |
|---------|-------------|
| `/status` | System status and health |
| `/metrics` | Performance data (24h) |
| `/health` | Full health check |
| `/pending` | Changes awaiting approval |
| `/approve <id>` | Approve a change |
| `/reject <id>` | Reject a change |
| `/task <description>` | Queue a new task |
| `/help` | List all commands |

### What You'll Receive

Your bot will automatically send you:

- 📊 **Daily updates** (9am) - System status and metrics
- 🔴 **Approval requests** - When system needs permission
- ⚠️ **Alerts** - If problems are detected
- ✅ **Confirmations** - When tasks complete

---

## Troubleshooting

### Bot doesn't respond

```bash
# Check tokens are set
echo $TELEGRAM_BOT_TOKEN
echo $TELEGRAM_CHAT_ID

# If empty, run setup again
./scripts/setup_telegram.sh
```

### Wrong chat ID

Your bot will only respond to the chat ID you configured. Make sure:
- You got the ID from @userinfobot
- You're messaging YOUR bot (not someone else's)

### Token invalid

If BotFather says token is invalid:
- Create a new bot (`/newbot` again)
- Use the new token

---

## Security Notes

- **Token = Password** - Keep it secret
- Never commit tokens to git
- Chat ID restricts who can use your bot
- Only you (with that chat ID) can control the system

---

## Need Help?

If setup fails, just ask in CLI:
```
I need help setting up Telegram bot
```

Or check detailed docs:
```bash
cat docs/COMMUNICATION_PROCEDURES.md
```
