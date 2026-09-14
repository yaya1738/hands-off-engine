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
