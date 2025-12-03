# Telegram Setup - Every Single Step

**You need:** Your phone with Telegram app installed

---

## PART 1: Get Two Numbers (On Your Phone)

### Step 1.1: Get Bot Token

1. **Open Telegram app on your phone**
2. **Click the search bar at the top**
3. **Type:** `@BotFather`
4. **Click on BotFather** (blue checkmark, official bot)
5. **Click "START"** at the bottom
6. **Type and send:** `/newbot`
7. **BotFather asks "Alright, a new bot. How are we going to call it?"**
   - **Type and send:** `My Hands Off Bot` (or any name you want)
8. **BotFather asks for username**
   - **Type and send:** `your_name_handsoff_bot` (must end in `bot`)
   - Example: `john_handsoff_bot`
9. **BotFather sends you a long message with a TOKEN**
   - Looks like: `7234567890:AAHdkE8FjkslDKF9dkfJDKFjdkf83jdkf`
10. **COPY this token** (long press on it → Copy)
11. **Paste it somewhere safe** (Notes app, email yourself, etc.)

✅ **You now have: Bot Token**

---

### Step 1.2: Get Chat ID

1. **Still in Telegram, click search again**
2. **Type:** `@userinfobot`
3. **Click on userinfobot**
4. **Click "START"** at the bottom
5. **Type and send any message:** `hi`
6. **Bot replies with your info, including "Id:"**
   - Looks like: `Id: 123456789` (just numbers)
7. **COPY the number** (the ID number)
8. **Paste it somewhere safe** (next to your bot token)

✅ **You now have: Chat ID**

---

## PART 2: Put Numbers in Server (On Your Computer)

### Step 2.1: Connect to Server

```bash
# You're already here if you're reading this in the terminal
cd /root/hands-off-engine
```

### Step 2.2: Save Your Bot Token

**Replace `YOUR_TOKEN_HERE` with the actual token you copied:**

```bash
echo 'export TELEGRAM_BOT_TOKEN="YOUR_TOKEN_HERE"' >> ~/.bashrc
```

**Real example (YOUR TOKEN WILL BE DIFFERENT):**
```bash
echo 'export TELEGRAM_BOT_TOKEN="7234567890:AAHdkE8FjkslDKF9dkfJDKFjdkf83jdkf"' >> ~/.bashrc
```

### Step 2.3: Save Your Chat ID

**Replace `YOUR_CHAT_ID_HERE` with the actual ID you copied:**

```bash
echo 'export TELEGRAM_CHAT_ID="YOUR_CHAT_ID_HERE"' >> ~/.bashrc
```

**Real example (YOUR ID WILL BE DIFFERENT):**
```bash
echo 'export TELEGRAM_CHAT_ID="123456789"' >> ~/.bashrc
```

### Step 2.4: Load the Settings

```bash
source ~/.bashrc
```

---

## PART 3: Test It Works

### Step 3.1: Test Send Message

```bash
cd /root/hands-off-engine
python3 -c "
import os, sys
sys.path.insert(0, '.')
from telegram.telegram_command_bot import TelegramCommandBot
bot = TelegramCommandBot()
result = bot.send_message('✅ Bot is working! Try sending /status')
print('Message sent!' if result else 'Failed to send')
"
```

### Step 3.2: Check Your Phone

**Go back to Telegram on your phone**
- You should see a message from your bot
- It says: "✅ Bot is working! Try sending /status"

### Step 3.3: Try a Command

**In Telegram, send to your bot:**
```
/status
```

**You should get back:** System status information

---

## ✅ DONE!

Your bot is working. You can now send these commands in Telegram:

- `/status` - System info
- `/metrics` - Performance data
- `/health` - Health check
- `/help` - See all commands

---

## If Something Doesn't Work

### "Failed to send" or no message received

**Check your tokens are saved:**
```bash
echo "Bot token: $TELEGRAM_BOT_TOKEN"
echo "Chat ID: $TELEGRAM_CHAT_ID"
```

- If they show empty, repeat Part 2
- Make sure you ran `source ~/.bashrc`

### "Bot doesn't respond to /status"

**Make sure you:**
- Are messaging YOUR bot (the one you created)
- Used the correct chat ID from @userinfobot
- The bot token is correct (no extra spaces)

### Start Over

If you want to start fresh:
```bash
# Remove old settings
sed -i '/TELEGRAM_BOT_TOKEN/d' ~/.bashrc
sed -i '/TELEGRAM_CHAT_ID/d' ~/.bashrc

# Now follow Part 1 and Part 2 again
```

---

## Summary: What You Need To Do

**PART 1 (Phone):**
1. Message @BotFather → Get token
2. Message @userinfobot → Get chat ID

**PART 2 (Server):**
1. Run: `echo 'export TELEGRAM_BOT_TOKEN="YOUR_TOKEN"' >> ~/.bashrc`
2. Run: `echo 'export TELEGRAM_CHAT_ID="YOUR_ID"' >> ~/.bashrc`
3. Run: `source ~/.bashrc`

**PART 3 (Test):**
1. Run the python test command
2. Check phone for message
3. Send `/status` to bot

That's it!
