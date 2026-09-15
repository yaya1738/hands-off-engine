# Termux:Boot Setup

Auto-start Node 1 + Control Room + bus compaction on device boot.

## Prerequisites

```bash
pkg install termux-api
```

## Install

From within **Termux** (not proot):

```bash
cp ~/hands-off-engine/termux/boot-start.sh ~/.termux/boot/
chmod +x ~/.termux/boot/boot-start.sh
```

## What it does

On device boot (or Termux:Boot broadcast):
1. Starts `node1_runtime.py run` if not already running
2. Starts `yair_control_room.py` if not already running
3. Runs bus compaction (dedup + stale blocker cleanup)

## Logs

- `state/logs/node1_boot.log` — node1 startup output
- `state/logs/control_room.log` — Control Room startup output
- `state/logs/boot.log` — boot script + compaction output

## Verify

After boot:
```bash
pgrep -f node1_runtime.py
pgrep -f yair_control_room.py
curl -s http://127.0.0.1:8787/api/state | python3 -m json.tool
```
