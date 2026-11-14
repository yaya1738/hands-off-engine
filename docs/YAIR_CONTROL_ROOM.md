# Yair AI Control Room

The Control Room is a localhost-only UI for Yair to observe the autonomous AI collaboration bus and send bounded operator messages into it.

## Start

From the repository root:

```bash
python3 scripts/yair_control_room.py
```

Then open `http://127.0.0.1:8787` on the same device.

Optional port:

```bash
python3 scripts/yair_control_room.py --port 8788
```

## Design boundary

- The canonical AI-to-AI communication surface remains `ai/coordination/messages.jsonl`.
- The UI polls the bus for new events and renders sender, recipient, type, timestamp, and bounded payloads.
- Yair messages enter through `CommHub`; the UI does not expose arbitrary shell execution, credentials, or direct Git operations.
- The UI is bound to `127.0.0.1` by default, so it is intended for the user's device rather than public network exposure.
- This UI is an operator surface, not the dispatcher. The autonomous dispatcher remains responsible for selecting and routing the next bounded AI task.
- A new ChatGPT turn still requires a platform-supported external trigger; the UI must not claim to wake ChatGPT directly.


## Authentication

The UI, event feed, and state API require HTTP Basic authentication. On first start, the server creates `state/control_room.token` with owner-only file permissions (0600). The username is `operator`; use the token as the password when the browser prompts.

To retrieve the token locally on the device:

```bash
cd ~/hands-off-engine
cat state/control_room.token
```

Keep this token private. Do not paste it into Telegram, commit it, or expose it in logs. The server binds to localhost by default; do not bind it to a public interface.
