#!/usr/bin/env python3
"""
SCRIBES - Dedicated watchers that record everything
Serving: Yair Siegel

Each scribe watches one stream and creates a running record.
Together they capture the full picture of the living system.

SCRIBES:
- Stage Scribe: Records the main self-conversation
- Gallery Scribe: Records observer reactions
- Message Scribe: Records all system communications
- Summary Scribe: Creates periodic summaries of everything
"""

import json
import time
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"
SCRIBE_DIR = STATE_DIR / "scribes"
SCRIBE_DIR.mkdir(exist_ok=True)

# Log files to watch
STAGE_LOG = STATE_DIR / "self_conversation.jsonl"
GALLERY_LOG = STATE_DIR / "peanut_gallery.jsonl"
MESSAGE_LOG = STATE_DIR / "message_bus.jsonl"

# Scribe output files
STAGE_RECORD = SCRIBE_DIR / "stage_record.md"
GALLERY_RECORD = SCRIBE_DIR / "gallery_record.md"
MESSAGE_RECORD = SCRIBE_DIR / "message_record.md"
FULL_CHRONICLE = SCRIBE_DIR / "full_chronicle.md"
SUMMARY_RECORD = SCRIBE_DIR / "summary.md"


class Scribe:
    """Base scribe class - watches and records."""

    def __init__(self, name: str, source_file: Path, output_file: Path):
        self.name = name
        self.source = source_file
        self.output = output_file
        self.lines_seen = 0
        self.entries = []
        self.running = False

    def _format_entry(self, entry: Dict) -> str:
        """Format a single entry for the record. Override in subclasses."""
        return json.dumps(entry)

    def _write_header(self):
        """Write the record header."""
        header = f"""# {self.name} Record
Generated: {datetime.now(timezone.utc).isoformat()}
Source: {self.source}

---

"""
        self.output.write_text(header)

    def _append_to_record(self, text: str):
        """Append formatted text to the record."""
        with open(self.output, "a") as f:
            f.write(text + "\n")

    def watch_once(self) -> List[Dict]:
        """Check for new entries and record them."""
        if not self.source.exists():
            return []

        new_entries = []
        with open(self.source) as f:
            lines = f.readlines()

        for line in lines[self.lines_seen:]:
            try:
                entry = json.loads(line.strip())
                new_entries.append(entry)
                formatted = self._format_entry(entry)
                self._append_to_record(formatted)
                self.entries.append(entry)
            except json.JSONDecodeError:
                pass

        self.lines_seen = len(lines)
        return new_entries

    def start_watching(self, interval: float = 5.0):
        """Start continuous watching."""
        self._write_header()
        self.running = True

        while self.running:
            new = self.watch_once()
            if new:
                print(f"[{self.name}] Recorded {len(new)} new entries")
            time.sleep(interval)

    def stop(self):
        """Stop watching."""
        self.running = False


class StageScribe(Scribe):
    """Records the main self-conversation (center stage)."""

    def __init__(self):
        super().__init__(
            name="Stage Scribe",
            source_file=STAGE_LOG,
            output_file=STAGE_RECORD,
        )
        self.turn_count = 0

    def _format_entry(self, entry: Dict) -> str:
        timestamp = entry.get("timestamp", "")[:19]
        role = entry.get("role", "unknown")
        content = entry.get("content", "")
        mode = entry.get("mode", "")

        if role == "system":
            return f"\n## Context\n```\n{content}\n```\n"
        elif role == "questioner":
            self.turn_count += 1
            return f"\n### Turn {self.turn_count} ({mode})\n\n**Question:** {content}\n"
        elif role == "responder":
            return f"\n**Response:**\n> {content}\n"
        elif role == "meta":
            return f"\n---\n*META-REFLECTION:* {content}\n---\n"
        else:
            return f"\n[{role}] {content}\n"


class GalleryScribe(Scribe):
    """Records the peanut gallery reactions."""

    def __init__(self):
        super().__init__(
            name="Gallery Scribe",
            source_file=GALLERY_LOG,
            output_file=GALLERY_RECORD,
        )
        self.member_reactions = defaultdict(list)

    def _format_entry(self, entry: Dict) -> str:
        timestamp = entry.get("timestamp", "")[:19]
        member = entry.get("member", "unknown")
        whisper = entry.get("whisper", "")
        context = entry.get("context", "")[:50]

        self.member_reactions[member].append(whisper)

        # Emoji mapping
        emojis = {
            "skeptic": "🤨",
            "optimist": "✨",
            "pragmatist": "⚙️",
            "contrarian": "🔄",
            "historian": "📚",
            "numbers_person": "📊",
        }
        emoji = emojis.get(member, "👤")

        return f"\n{emoji} **{member.title()}** _{timestamp}_\n> {whisper}\n> *(reacting to: \"{context}...\")*\n"


class MessageScribe(Scribe):
    """Records all system messages."""

    def __init__(self):
        super().__init__(
            name="Message Scribe",
            source_file=MESSAGE_LOG,
            output_file=MESSAGE_RECORD,
        )
        self.message_counts = defaultdict(int)
        self.conversations = defaultdict(list)

    def _format_entry(self, entry: Dict) -> str:
        timestamp = entry.get("timestamp", "")[:19]
        sender = entry.get("sender", "unknown")
        recipient = entry.get("recipient", "unknown")
        msg_type = entry.get("message_type", "message")
        content = entry.get("content", "")
        urgency = entry.get("urgency", "normal")

        self.message_counts[sender] += 1

        # Type emoji
        type_emojis = {
            "observation": "👁️",
            "command": "⚡",
            "response": "💬",
            "conversation": "🗣️",
            "reality_check": "🌍",
            "announcement": "📢",
        }
        emoji = type_emojis.get(msg_type, "📨")

        urgency_marker = "🔴 " if urgency == "critical" else "🟡 " if urgency == "high" else ""

        return f"\n{urgency_marker}{emoji} **{sender}** → **{recipient}** _{timestamp}_\n> [{msg_type}] {content[:200]}\n"


class SummaryScribe:
    """Creates periodic summaries of all activity."""

    def __init__(self, scribes: List[Scribe]):
        self.scribes = scribes
        self.output = SUMMARY_RECORD
        self.summaries = []

    def create_summary(self) -> str:
        """Create a summary of current activity."""
        now = datetime.now(timezone.utc)

        summary_parts = [
            f"# System Summary",
            f"Generated: {now.isoformat()}",
            "",
            "---",
            "",
        ]

        # Stage summary
        stage_scribe = next((s for s in self.scribes if isinstance(s, StageScribe)), None)
        if stage_scribe:
            summary_parts.extend([
                "## Center Stage",
                f"- Turns completed: {stage_scribe.turn_count}",
                f"- Total entries: {len(stage_scribe.entries)}",
                "",
            ])
            # Last few insights
            recent = [e for e in stage_scribe.entries[-5:] if e.get("role") == "responder"]
            if recent:
                summary_parts.append("**Recent insights:**")
                for r in recent:
                    content = r.get("content", "")[:100]
                    summary_parts.append(f"- {content}...")
                summary_parts.append("")

        # Gallery summary
        gallery_scribe = next((s for s in self.scribes if isinstance(s, GalleryScribe)), None)
        if gallery_scribe:
            summary_parts.extend([
                "## Peanut Gallery",
                f"- Total reactions: {len(gallery_scribe.entries)}",
                "",
            ])
            # Reactions by member
            for member, reactions in gallery_scribe.member_reactions.items():
                summary_parts.append(f"- {member}: {len(reactions)} reactions")
            summary_parts.append("")

        # Message summary
        message_scribe = next((s for s in self.scribes if isinstance(s, MessageScribe)), None)
        if message_scribe:
            summary_parts.extend([
                "## System Messages",
                f"- Total messages: {len(message_scribe.entries)}",
                "",
            ])
            # Messages by sender
            for sender, count in sorted(message_scribe.message_counts.items(), key=lambda x: -x[1])[:5]:
                summary_parts.append(f"- {sender}: {count} messages")
            summary_parts.append("")

        # Key themes
        summary_parts.extend([
            "## Key Themes",
            "",
        ])

        all_content = []
        for scribe in self.scribes:
            for entry in scribe.entries:
                content = entry.get("content", "") or entry.get("whisper", "")
                all_content.append(content.lower())

        combined = " ".join(all_content)

        themes = []
        if "action" in combined:
            themes.append("- 🎯 Action bias - focus on doing")
        if "$0" in combined or "zero" in combined:
            themes.append("- 💰 Income focus - $0 is the problem")
        if "conversion" in combined:
            themes.append("- 📊 Conversion optimization")
        if "proof" in combined or "evidence" in combined:
            themes.append("- 🔍 Need for proof/evidence")
        if "opposite" in combined or "alternative" in combined:
            themes.append("- 🔄 Contrarian thinking")

        if themes:
            summary_parts.extend(themes)
        else:
            summary_parts.append("- No clear themes yet")

        summary = "\n".join(summary_parts)
        self.output.write_text(summary)
        self.summaries.append({"timestamp": now.isoformat(), "content": summary})

        return summary


class ChronicleScribe:
    """Creates a unified chronicle of everything in chronological order."""

    def __init__(self):
        self.output = FULL_CHRONICLE
        self.all_events = []

    def compile_chronicle(self):
        """Compile all events into a single chronological record."""
        events = []

        # Gather from all sources
        for source, source_type in [
            (STAGE_LOG, "stage"),
            (GALLERY_LOG, "gallery"),
            (MESSAGE_LOG, "message"),
        ]:
            if source.exists():
                with open(source) as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            entry["_source"] = source_type
                            events.append(entry)
                        except:
                            pass

        # Sort by timestamp
        events.sort(key=lambda x: x.get("timestamp", ""))

        # Write chronicle
        lines = [
            "# Full System Chronicle",
            f"Compiled: {datetime.now(timezone.utc).isoformat()}",
            "",
            "---",
            "",
        ]

        for event in events:
            ts = event.get("timestamp", "")[:19]
            source = event.get("_source", "unknown")

            if source == "stage":
                role = event.get("role", "")
                content = event.get("content", "")[:150]
                lines.append(f"**{ts}** 🎭 [{role}] {content}")

            elif source == "gallery":
                member = event.get("member", "")
                whisper = event.get("whisper", "")[:100]
                lines.append(f"**{ts}** 👁️ [{member}] {whisper}")

            elif source == "message":
                sender = event.get("sender", "")
                recipient = event.get("recipient", "")
                content = event.get("content", "")[:100]
                lines.append(f"**{ts}** 📨 {sender}→{recipient}: {content}")

            lines.append("")

        self.output.write_text("\n".join(lines))
        self.all_events = events
        return len(events)


class ScribeCoordinator:
    """Coordinates all scribes working together."""

    def __init__(self):
        self.stage_scribe = StageScribe()
        self.gallery_scribe = GalleryScribe()
        self.message_scribe = MessageScribe()
        self.summary_scribe = SummaryScribe([
            self.stage_scribe,
            self.gallery_scribe,
            self.message_scribe,
        ])
        self.chronicle_scribe = ChronicleScribe()
        self.running = False

    def run_all(self, duration_minutes: int = 60, summary_interval: int = 5):
        """Run all scribes for a duration."""
        print("=" * 70)
        print("📜 SCRIBES ACTIVATED")
        print("=" * 70)
        print("\nScribes taking their positions:")
        print("  📝 Stage Scribe - watching center stage")
        print("  📝 Gallery Scribe - recording reactions")
        print("  📝 Message Scribe - logging all communications")
        print("  📝 Summary Scribe - creating periodic summaries")
        print("  📝 Chronicle Scribe - compiling full record")
        print()

        # Initialize all record files
        for scribe in [self.stage_scribe, self.gallery_scribe, self.message_scribe]:
            scribe._write_header()

        self.running = True
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        last_summary = start_time

        while self.running and time.time() < end_time:
            # Each scribe watches their source
            stage_new = self.stage_scribe.watch_once()
            gallery_new = self.gallery_scribe.watch_once()
            message_new = self.message_scribe.watch_once()

            # Report activity
            total_new = len(stage_new) + len(gallery_new) + len(message_new)
            if total_new > 0:
                elapsed = int(time.time() - start_time)
                print(f"[{elapsed}s] Recorded: Stage={len(stage_new)}, Gallery={len(gallery_new)}, Messages={len(message_new)}")

            # Periodic summary
            if time.time() - last_summary > summary_interval * 60:
                print("\n[Creating summary...]")
                self.summary_scribe.create_summary()
                last_summary = time.time()

            time.sleep(5)

        # Final compilation
        print("\n[Compiling full chronicle...]")
        total = self.chronicle_scribe.compile_chronicle()
        self.summary_scribe.create_summary()

        print("\n" + "=" * 70)
        print("📜 SCRIBES COMPLETE")
        print("=" * 70)
        print(f"\nRecords created:")
        print(f"  📄 {STAGE_RECORD}")
        print(f"  📄 {GALLERY_RECORD}")
        print(f"  📄 {MESSAGE_RECORD}")
        print(f"  📄 {FULL_CHRONICLE}")
        print(f"  📄 {SUMMARY_RECORD}")
        print(f"\nTotal events chronicled: {total}")

    def stop(self):
        self.running = False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Scribes - Record everything")
    parser.add_argument("command", choices=["start", "compile", "summary", "status"])
    parser.add_argument("--duration", type=int, default=60, help="Duration in minutes")

    args = parser.parse_args()

    coordinator = ScribeCoordinator()

    if args.command == "start":
        coordinator.run_all(duration_minutes=args.duration)

    elif args.command == "compile":
        chronicle = ChronicleScribe()
        total = chronicle.compile_chronicle()
        print(f"Chronicle compiled: {total} events")
        print(f"Output: {FULL_CHRONICLE}")

    elif args.command == "summary":
        # Quick summary of current state
        stage = StageScribe()
        gallery = GalleryScribe()
        message = MessageScribe()

        stage.watch_once()
        gallery.watch_once()
        message.watch_once()

        summary = SummaryScribe([stage, gallery, message])
        result = summary.create_summary()
        print(result)

    elif args.command == "status":
        print(f"\n{'='*60}")
        print("SCRIBE STATUS")
        print(f"{'='*60}")

        for path in [STAGE_RECORD, GALLERY_RECORD, MESSAGE_RECORD, FULL_CHRONICLE, SUMMARY_RECORD]:
            exists = "✓" if path.exists() else "✗"
            size = path.stat().st_size if path.exists() else 0
            print(f"  {exists} {path.name}: {size} bytes")


if __name__ == "__main__":
    main()
