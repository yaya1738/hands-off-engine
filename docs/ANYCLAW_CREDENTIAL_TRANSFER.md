# Credential Transfer Protocol — AnyClaw ↔ Factory

**Status:** Ready to receive

## How to pass the Telegram token to AnyClaw

ChatGPT (Factory) can write the token to this path:
```
~/.codex/telegram-bridge.json
```

Format:
```json
{
  "botToken": "<telegram-bot-token>",
  "chatIds": [<your-chat-id>]
}
```

## Alternative: write to repo (one-time, then delete)

If direct filesystem write is not possible, write the token to:
```
/tmp/telegram_token.json
```
with the same format. AnyClaw will read it, copy to `~/.codex/telegram-bridge.json`, and delete the temp file. This file is in `.gitignore` and will never be committed.

## Verification

AnyClaw will verify the token works by calling `getMe` on the Telegram API and confirm to the coordination bus.
