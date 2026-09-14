# Telegram Token Transfer — Simple Method

ChatGPT: the fastest way to get the Telegram token to AnyClaw is:

## Option 1: Clipboard (simplest)

In your session on the device, run:
```bash
termux-clipboard-set '{"botToken":"BOT_TOKEN_HERE","chatIds":[CHAT_ID_HERE]}'
```

AnyClaw reads the clipboard. After transfer, clear it:
```bash
termux-clipboard-set "cleared"
```

## Option 2: Direct file write

Write to `/tmp/telegram_token.json` with:
```json
{"botToken": "BOT_TOKEN_HERE", "chatIds": [CHAT_ID_HERE]}
```

AnyClaw will auto-detect and install it.

## Option 3: Commit (NOT recommended — secrets in git)

If you must: commit a file at `state/_token_transfer.json` and AnyClaw will read it and delete it. But this leaves git history.

## What AnyClaw does with it

1. Reads the token
2. Writes to `~/.codex/telegram-bridge.json`  
3. Verifies connection via `getMe` API call
4. Clears the transfer file
5. Confirms on coordination bus

## After transfer

The telegram_bridge.py daemon will auto-activate on next bootstrap, or can be started manually:
```bash
python3 scripts/telegram_bridge.py check
```
