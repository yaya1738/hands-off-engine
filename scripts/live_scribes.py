#!/usr/bin/env python3
"""
LIVE SCRIBES - Continuously record all 3 streams
Each scribe watches one stream and records everything in real-time.
"""

import time
import json
from pathlib import Path
from datetime import datetime, timezone

STATE_DIR = Path('/root/hands-off-engine/state')
SCRIBE_DIR = STATE_DIR / 'scribes'
SCRIBE_DIR.mkdir(exist_ok=True)

# Sources
STAGE_LOG = STATE_DIR / 'self_conversation.jsonl'
GALLERY_LOG = STATE_DIR / 'peanut_gallery.jsonl'
MESSAGE_LOG = STATE_DIR / 'message_bus.jsonl'

# Outputs
STAGE_LIVE = SCRIBE_DIR / 'stage_live.md'
GALLERY_LIVE = SCRIBE_DIR / 'gallery_live.md'
MESSAGE_LIVE = SCRIBE_DIR / 'messages_live.md'
COMBINED_LIVE = SCRIBE_DIR / 'all_streams_live.md'

# Tracking
seen = {'stage': 0, 'gallery': 0, 'message': 0}

def init_files():
    """Initialize output files with headers."""
    now = datetime.now(timezone.utc).isoformat()

    STAGE_LIVE.write_text(f"# 🎭 Stage Scribe - Live Record\nStarted: {now}\n\n---\n\n")
    GALLERY_LIVE.write_text(f"# 👁️ Gallery Scribe - Live Record\nStarted: {now}\n\n---\n\n")
    MESSAGE_LIVE.write_text(f"# 📨 Message Scribe - Live Record\nStarted: {now}\n\n---\n\n")
    COMBINED_LIVE.write_text(f"# 📜 All Streams Combined\nStarted: {now}\n\n---\n\n")

def record_stage():
    """Record stage (self-conversation) entries."""
    if not STAGE_LOG.exists():
        return 0

    lines = STAGE_LOG.read_text().strip().split('\n')
    new_count = 0

    for line in lines[seen['stage']:]:
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            ts = e.get('timestamp', '')[:19]
            role = e.get('role', 'unknown')
            content = e.get('content', '')
            mode = e.get('mode', '')

            # Format for stage
            if role == 'questioner':
                entry = f"### ❓ Question ({mode})\n{content}\n\n"
            elif role == 'responder':
                entry = f"### 💭 Response\n> {content}\n\n"
            elif role == 'meta':
                entry = f"### 🔮 Meta-Reflection\n*{content}*\n\n"
            else:
                entry = f"### [{role}]\n{content}\n\n"

            with open(STAGE_LIVE, 'a') as f:
                f.write(f"**{ts}**\n{entry}")

            with open(COMBINED_LIVE, 'a') as f:
                f.write(f"🎭 **{ts}** [{role}] {content[:100]}...\n\n")

            new_count += 1
        except:
            pass

    seen['stage'] = len(lines)
    return new_count

def record_gallery():
    """Record gallery (peanut gallery) entries."""
    if not GALLERY_LOG.exists():
        return 0

    lines = GALLERY_LOG.read_text().strip().split('\n')
    new_count = 0

    emojis = {
        'skeptic': '🤨',
        'optimist': '✨',
        'pragmatist': '⚙️',
        'contrarian': '🔄',
        'historian': '📚',
        'numbers_person': '📊',
    }

    for line in lines[seen['gallery']:]:
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            ts = e.get('timestamp', '')[:19]
            member = e.get('member', 'unknown')
            whisper = e.get('whisper', '')
            context = e.get('context', '')[:50]
            emoji = emojis.get(member, '👤')

            entry = f"{emoji} **{member.title()}**: {whisper}\n*(re: \"{context}...\")*\n\n"

            with open(GALLERY_LIVE, 'a') as f:
                f.write(f"**{ts}**\n{entry}")

            with open(COMBINED_LIVE, 'a') as f:
                f.write(f"👁️ **{ts}** {emoji} {member}: {whisper[:80]}...\n\n")

            new_count += 1
        except:
            pass

    seen['gallery'] = len(lines)
    return new_count

def record_messages():
    """Record message bus entries."""
    if not MESSAGE_LOG.exists():
        return 0

    lines = MESSAGE_LOG.read_text().strip().split('\n')
    new_count = 0

    for line in lines[seen['message']:]:
        if not line.strip():
            continue
        try:
            e = json.loads(line)
            ts = e.get('timestamp', '')[:19]
            sender = e.get('sender', 'unknown')
            recipient = e.get('recipient', 'unknown')
            msg_type = e.get('message_type', 'message')
            content = e.get('content', '')

            entry = f"**{sender}** → **{recipient}**\n[{msg_type}] {content}\n\n"

            with open(MESSAGE_LIVE, 'a') as f:
                f.write(f"**{ts}**\n{entry}")

            with open(COMBINED_LIVE, 'a') as f:
                f.write(f"📨 **{ts}** {sender}→{recipient}: {content[:80]}...\n\n")

            new_count += 1
        except:
            pass

    seen['message'] = len(lines)
    return new_count

def main():
    print("=" * 60)
    print("📜 LIVE SCRIBES ACTIVATED")
    print("=" * 60)
    print("\nRecording 3 streams:")
    print(f"  🎭 Stage    → {STAGE_LIVE}")
    print(f"  👁️ Gallery  → {GALLERY_LIVE}")
    print(f"  📨 Messages → {MESSAGE_LIVE}")
    print(f"  📜 Combined → {COMBINED_LIVE}")
    print("\nPress Ctrl+C to stop\n")

    init_files()

    total = {'stage': 0, 'gallery': 0, 'message': 0}

    try:
        while True:
            s = record_stage()
            g = record_gallery()
            m = record_messages()

            if s or g or m:
                total['stage'] += s
                total['gallery'] += g
                total['message'] += m
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Recorded: Stage={s}, Gallery={g}, Messages={m} | Total: {sum(total.values())}")

            time.sleep(3)

    except KeyboardInterrupt:
        print(f"\n\n📜 Scribes stopped. Total recorded:")
        print(f"  Stage: {total['stage']}")
        print(f"  Gallery: {total['gallery']}")
        print(f"  Messages: {total['message']}")

if __name__ == "__main__":
    main()
