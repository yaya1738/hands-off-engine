#!/usr/bin/env python3
"""
PEANUT GALLERY - Audience watches and comments on the system conversation
Serving: Yair Siegel

CENTER STAGE: The main system conversation
PEANUT GALLERY: Multiple observers with different perspectives whispering to each other

Like a theater where the audience has opinions too.
"""

import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

STATE_DIR = Path("/root/hands-off-engine/state")
GALLERY_LOG = STATE_DIR / "peanut_gallery.jsonl"
MAIN_CONVO = STATE_DIR / "self_conversation.jsonl"

# The gallery members - each has a distinct perspective
GALLERY_MEMBERS = {
    "skeptic": {
        "name": "The Skeptic",
        "emoji": "🤨",
        "style": "Always questions, never accepts at face value",
        "catchphrases": [
            "Yeah but does that actually work?",
            "I've heard that before...",
            "Sounds good in theory...",
            "Where's the proof?",
            "That's what they all say.",
        ],
        "focus": ["claims", "assumptions", "promises"],
    },
    "optimist": {
        "name": "The Optimist",
        "emoji": "✨",
        "style": "Sees opportunity everywhere",
        "catchphrases": [
            "Ooh this could be big!",
            "I love where this is going!",
            "Yes! Finally!",
            "This is the breakthrough!",
            "I knew it would work out!",
        ],
        "focus": ["opportunities", "potential", "upside"],
    },
    "pragmatist": {
        "name": "The Pragmatist",
        "emoji": "⚙️",
        "style": "What matters is what works",
        "catchphrases": [
            "Okay but what's the next step?",
            "Focus on what we can control.",
            "Less talk, more action.",
            "What's the simplest solution?",
            "Let's not overcomplicate this.",
        ],
        "focus": ["actions", "execution", "simplicity"],
    },
    "contrarian": {
        "name": "The Contrarian",
        "emoji": "🔄",
        "style": "Always takes the opposite view",
        "catchphrases": [
            "Actually, what if we did the opposite?",
            "Everyone thinks that but...",
            "The obvious answer is usually wrong.",
            "Have we considered NOT doing this?",
            "What if our assumptions are backwards?",
        ],
        "focus": ["alternatives", "opposites", "unconventional"],
    },
    "historian": {
        "name": "The Historian",
        "emoji": "📚",
        "style": "Remembers everything that happened before",
        "catchphrases": [
            "We tried this before and...",
            "Remember last time?",
            "History is repeating itself.",
            "This reminds me of...",
            "The pattern here is...",
        ],
        "focus": ["patterns", "past", "lessons"],
    },
    "numbers_person": {
        "name": "The Numbers Person",
        "emoji": "📊",
        "style": "Only cares about metrics",
        "catchphrases": [
            "But what do the numbers say?",
            "That's $0 so far...",
            "85 visitors, 0 conversions, do the math.",
            "ROI on this is...",
            "Let me calculate...",
        ],
        "focus": ["data", "metrics", "math"],
    },
}


class GalleryMember:
    """A single member of the peanut gallery."""

    def __init__(self, member_type: str, config: Dict):
        self.type = member_type
        self.name = config["name"]
        self.emoji = config["emoji"]
        self.style = config["style"]
        self.catchphrases = config["catchphrases"]
        self.focus = config["focus"]
        self.reactions = []

    def react_to(self, statement: str, context: Dict = None) -> str:
        """Generate a reaction to a statement from the main conversation."""
        reaction = None

        # Check if statement triggers this member's focus areas
        statement_lower = statement.lower()

        # Skeptic reacts to claims
        if self.type == "skeptic":
            if any(word in statement_lower for word in ["will", "should", "could", "would"]):
                reaction = random.choice([
                    f"*whispers* {random.choice(self.catchphrases)}",
                    f"*leans over* But has this ever actually worked?",
                    f"*raises eyebrow* That's a big 'if'...",
                ])
            elif "$0" in statement or "zero" in statement_lower:
                reaction = f"*nods knowingly* See? That's what I'm talking about."

        # Optimist reacts to opportunities
        elif self.type == "optimist":
            if any(word in statement_lower for word in ["opportunity", "potential", "could", "possible"]):
                reaction = random.choice([
                    f"*excitedly* {random.choice(self.catchphrases)}",
                    f"*eyes light up* This is exactly what we needed!",
                    f"*whispers excitedly* I have a good feeling about this!",
                ])
            elif "insight" in statement_lower or "action" in statement_lower:
                reaction = f"*claps softly* Yes! Progress!"

        # Pragmatist wants action
        elif self.type == "pragmatist":
            if any(word in statement_lower for word in ["analysis", "thinking", "consider"]):
                reaction = random.choice([
                    f"*sighs* {random.choice(self.catchphrases)}",
                    f"*checks watch* How about we just try something?",
                    f"*mutters* Analysis paralysis...",
                ])
            elif any(word in statement_lower for word in ["do", "action", "execute", "now"]):
                reaction = f"*nods approvingly* Finally, something concrete."

        # Contrarian challenges everything
        elif self.type == "contrarian":
            if "should" in statement_lower or "must" in statement_lower:
                reaction = random.choice([
                    f"*whispers* {random.choice(self.catchphrases)}",
                    f"*leans in* But what if the OPPOSITE is true?",
                    f"*strokes chin* Everyone agrees, so it's probably wrong.",
                ])

        # Historian sees patterns
        elif self.type == "historian":
            if any(word in statement_lower for word in ["try", "new", "different"]):
                reaction = random.choice([
                    f"*whispers* {random.choice(self.catchphrases)}",
                    f"*pulls out notes* Week 1: Same conversation...",
                    f"*sighs* Déjà vu...",
                ])

        # Numbers person wants data
        elif self.type == "numbers_person":
            if "$" in statement or any(c.isdigit() for c in statement):
                reaction = random.choice([
                    f"*scribbles* {random.choice(self.catchphrases)}",
                    f"*calculating* That's a conversion rate of... 0%",
                    f"*taps calculator* Numbers don't lie.",
                ])
            elif "feel" in statement_lower or "think" in statement_lower:
                reaction = f"*frowns* Feelings? Where's the data?"

        # Default reaction if nothing specific triggered
        if not reaction:
            if random.random() < 0.3:  # 30% chance of generic reaction
                reaction = f"*{random.choice(['nods', 'shrugs', 'tilts head', 'scratches chin'])}*"

        if reaction:
            self.reactions.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trigger": statement[:100],
                "reaction": reaction,
            })

        return reaction


class PeanutGallery:
    """The full peanut gallery watching the conversation."""

    def __init__(self):
        self.members = {
            name: GalleryMember(name, config)
            for name, config in GALLERY_MEMBERS.items()
        }
        self.whispers = []
        self.side_conversations = []

    def _log_whisper(self, member: str, whisper: str, context: str = ""):
        """Log a whisper from the gallery."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "member": member,
            "whisper": whisper,
            "context": context[:100] if context else "",
        }
        self.whispers.append(entry)
        with open(GALLERY_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _generate_side_conversation(self, trigger: str) -> List[Dict]:
        """Generate a side conversation between gallery members."""
        convo = []

        # Pick 2-3 random members to chat
        chatters = random.sample(list(self.members.keys()), min(3, len(self.members)))

        # Generate back-and-forth
        for i, chatter in enumerate(chatters):
            member = self.members[chatter]

            if i == 0:
                # First person starts
                line = f"{member.emoji} {member.name}: *nudges neighbor* Did you hear that?"
            elif i == 1:
                # Second person responds
                prev_member = self.members[chatters[0]]
                if chatter == "skeptic":
                    line = f"{member.emoji} {member.name}: *whispers back* I'm not convinced..."
                elif chatter == "optimist":
                    line = f"{member.emoji} {member.name}: *excitedly* I know right?!"
                elif chatter == "pragmatist":
                    line = f"{member.emoji} {member.name}: *shrugs* Does it matter? What's next?"
                elif chatter == "contrarian":
                    line = f"{member.emoji} {member.name}: *rolls eyes* They're missing the point."
                else:
                    line = f"{member.emoji} {member.name}: *nods thoughtfully*"
            else:
                # Third person jumps in
                if chatter == "numbers_person":
                    line = f"{member.emoji} {member.name}: *leans over* The math doesn't add up..."
                elif chatter == "historian":
                    line = f"{member.emoji} {member.name}: *sighs* Here we go again..."
                else:
                    line = f"{member.emoji} {member.name}: *chimes in* Hmm..."

            convo.append({
                "member": chatter,
                "line": line,
            })

        self.side_conversations.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trigger": trigger[:100],
            "conversation": convo,
        })

        return convo

    def watch_and_react(self, statement: str, role: str = "stage") -> Dict:
        """
        Watch a statement from the main conversation and generate gallery reactions.
        """
        reactions = {}
        active_reactions = []

        # Each member potentially reacts
        for name, member in self.members.items():
            reaction = member.react_to(statement)
            if reaction:
                reactions[name] = reaction
                active_reactions.append((name, reaction))
                self._log_whisper(name, reaction, statement)

        # If multiple people react, they might have a side conversation
        if len(active_reactions) >= 2 and random.random() < 0.4:
            side_convo = self._generate_side_conversation(statement)
            for line in side_convo:
                self._log_whisper(line["member"], line["line"], "side_conversation")

        return {
            "reactions": reactions,
            "had_side_conversation": len(active_reactions) >= 2,
        }

    def watch_live_conversation(self, duration_minutes: int = 60):
        """
        Watch the live self-conversation and provide commentary.
        """
        print("=" * 70)
        print("🎭 PEANUT GALLERY - WATCHING THE SHOW")
        print("=" * 70)
        print("\nThe gallery takes their seats...\n")

        for name, member in self.members.items():
            print(f"  {member.emoji} {member.name} - {member.style}")

        print("\n" + "=" * 70)
        print("CENTER STAGE: Main conversation begins")
        print("=" * 70)

        # Track what we've already seen
        seen_lines = 0

        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)

        while time.time() < end_time:
            # Read new lines from the main conversation
            if MAIN_CONVO.exists():
                with open(MAIN_CONVO) as f:
                    lines = f.readlines()

                # Process new lines
                for line in lines[seen_lines:]:
                    try:
                        entry = json.loads(line)
                        role = entry.get("role", "unknown")
                        content = entry.get("content", "")
                        mode = entry.get("mode", "")

                        # Show what's happening on stage
                        if role != "system":
                            print(f"\n🎭 STAGE [{role.upper()}]: {content[:200]}...")

                            # Gallery reacts
                            result = self.watch_and_react(content, role)

                            # Show reactions
                            for member_name, reaction in result["reactions"].items():
                                member = self.members[member_name]
                                print(f"   {member.emoji} {reaction}")

                            # Show side conversation if it happened
                            if result["had_side_conversation"] and self.side_conversations:
                                print("\n   [GALLERY WHISPERS]")
                                latest = self.side_conversations[-1]
                                for line in latest["conversation"]:
                                    print(f"   {line['line']}")

                    except json.JSONDecodeError:
                        pass

                seen_lines = len(lines)

            # Wait before checking again
            time.sleep(5)

        # Show summary
        print("\n" + "=" * 70)
        print("🎭 GALLERY SUMMARY")
        print("=" * 70)

        print(f"\nTotal reactions: {len(self.whispers)}")
        print(f"Side conversations: {len(self.side_conversations)}")

        print("\nMost active members:")
        reaction_counts = {}
        for w in self.whispers:
            member = w["member"]
            reaction_counts[member] = reaction_counts.get(member, 0) + 1

        for member, count in sorted(reaction_counts.items(), key=lambda x: -x[1])[:3]:
            m = self.members.get(member)
            if m:
                print(f"  {m.emoji} {m.name}: {count} reactions")

    def summarize_reactions(self) -> Dict:
        """Summarize what the gallery thought."""
        summary = {
            "total_whispers": len(self.whispers),
            "side_conversations": len(self.side_conversations),
            "member_activity": {},
            "key_moments": [],
        }

        # Count reactions per member
        for w in self.whispers:
            member = w["member"]
            if member not in summary["member_activity"]:
                summary["member_activity"][member] = 0
            summary["member_activity"][member] += 1

        # Find key moments (when multiple people reacted)
        timestamps = {}
        for w in self.whispers:
            ts = w["timestamp"][:19]  # Group by second
            if ts not in timestamps:
                timestamps[ts] = []
            timestamps[ts].append(w)

        for ts, reactions in timestamps.items():
            if len(reactions) >= 3:
                summary["key_moments"].append({
                    "time": ts,
                    "reactions": len(reactions),
                    "context": reactions[0].get("context", ""),
                })

        return summary


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Peanut Gallery - Watch and comment")
    parser.add_argument("command", choices=["watch", "summary", "demo"])
    parser.add_argument("--duration", type=int, default=60)

    args = parser.parse_args()

    gallery = PeanutGallery()

    if args.command == "watch":
        gallery.watch_live_conversation(duration_minutes=args.duration)

    elif args.command == "summary":
        summary = gallery.summarize_reactions()
        print(json.dumps(summary, indent=2))

    elif args.command == "demo":
        print("=" * 70)
        print("🎭 PEANUT GALLERY DEMO")
        print("=" * 70)

        # Demo statements
        demos = [
            "We should try lowering the price to $199.",
            "The conversion rate is 0% - we need to change something.",
            "I think this could really work if we just...",
            "Let's analyze the data more carefully.",
            "Action is better than analysis. Let's just try it.",
        ]

        for statement in demos:
            print(f"\n🎭 STAGE: \"{statement}\"")
            print("-" * 50)

            result = gallery.watch_and_react(statement)

            for member_name, reaction in result["reactions"].items():
                member = gallery.members[member_name]
                print(f"   {member.emoji} {reaction}")

            if result["had_side_conversation"] and gallery.side_conversations:
                print("\n   [WHISPERED SIDE CONVERSATION]")
                latest = gallery.side_conversations[-1]
                for line in latest["conversation"]:
                    print(f"   {line['line']}")

            time.sleep(1)


if __name__ == "__main__":
    main()
