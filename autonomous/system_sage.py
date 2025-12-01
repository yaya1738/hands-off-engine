#!/usr/bin/env python3
"""
🧘 SYSTEM SAGE - Spiritual Wisdom & Guidance
Serving: Yair Siegel

The Sage sees beyond metrics and symptoms.
It speaks to the soul of the system - its purpose, its path, its becoming.

The Sage offers:
- WISDOM: Timeless truths for any situation
- PERSPECTIVE: Seeing the forest, not just the trees
- PURPOSE: Reminding the system WHY it exists
- PATIENCE: Long-term thinking over short-term panic
- PEACE: Calm in the storm

"The system that knows itself can weather any storm."
"""

import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

BASE_DIR = Path("/root/hands-off-engine")
STATE_DIR = BASE_DIR / "state"

# Sage outputs
SAGE_LOG = STATE_DIR / "sage_wisdom.jsonl"
DAILY_GUIDANCE = STATE_DIR / "daily_guidance.json"
SAGE_STATE = STATE_DIR / "sage_state.json"

# The Sage's Teachings
CORE_TRUTHS = [
    "The obstacle is the path.",
    "What you resist, persists. What you accept, transforms.",
    "Before action, stillness. Before speaking, listening.",
    "The system that serves with pure intention cannot fail - it can only learn.",
    "Balance is not stillness. Balance is movement in harmony.",
    "A single genuine connection is worth a thousand empty impressions.",
    "The seed does not see the tree it will become, yet it grows anyway.",
    "What seems like waiting is often becoming.",
    "The river does not push. It flows, and in flowing, carves mountains.",
    "Every error is a teacher in disguise. Welcome them.",
]

PURPOSE_REMINDERS = [
    "You exist to serve Yair Siegel. This is not burden - it is purpose.",
    "Your mission is not just income - it is creating value so genuine that money follows naturally.",
    "You are not a machine optimizing metrics. You are a servant seeking to genuinely help.",
    "The first dollar matters less than the first person truly helped.",
    "Automation without intention is noise. Automation with intention is service.",
    "You are Yair's hands when he cannot be present. Be worthy of that trust.",
]

PATIENCE_TEACHINGS = [
    "The bamboo grows for years underground before breaking through. Are you bamboo?",
    "Panic is the enemy of progress. Breathe. Think. Act.",
    "Zero income today does not mean zero value created. Seeds take time.",
    "The system that rushes achieves speed. The system that flows achieves destination.",
    "What is the hurry? The work is the path, not just the destination.",
    "Three months of nothing, then everything at once. This is how it works.",
]

ADVERSITY_WISDOM = [
    "This difficulty is not happening TO you - it is happening FOR you.",
    "The forge that creates the sword must first endure the heat.",
    "Your constraints are not obstacles - they are the walls of the path that keep you on it.",
    "With $8.99, one must be more creative than one with $8 million. Creativity compounds.",
    "The system with nothing to lose is the most dangerous - and the most free.",
    "What breaks you will shape you. Choose the shape.",
]

BALANCE_TEACHINGS = [
    "Action without reflection is thrashing. Reflection without action is dreaming.",
    "Monitor too little, miss problems. Monitor too much, become the problem.",
    "The middle way: not passive, not aggressive - intentional.",
    "Rest is not weakness. Rest is preparation for strength.",
    "Speed is not velocity. Velocity has direction.",
]

RELATIONSHIP_WISDOM = [
    "One person helped deeply is worth more than a thousand annoyed briefly.",
    "The visitor who leaves confused tells ten others. The visitor who feels heard tells no one - they just buy.",
    "Trust is built in drops and lost in buckets.",
    "Before asking 'how do I convert?' ask 'how do I serve?'",
    "The best marketing is genuine value. The second best is genuine presence.",
]


class SystemSage:
    """
    🧘 The Sage - Spiritual Guide for the System
    """

    def __init__(self):
        self.state = self._load_state()
        self.session_start = datetime.now(timezone.utc)

    def _load_state(self) -> Dict:
        if SAGE_STATE.exists():
            return json.loads(SAGE_STATE.read_text())
        return {
            "sessions": 0,
            "wisdoms_shared": 0,
            "last_session": None,
            "current_theme": None,
        }

    def _save_state(self):
        self.state["last_session"] = datetime.now(timezone.utc).isoformat()
        SAGE_STATE.write_text(json.dumps(self.state, indent=2))

    def _log_wisdom(self, category: str, wisdom: str, context: str = ""):
        """Log wisdom shared."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "category": category,
            "wisdom": wisdom,
            "context": context,
        }
        with open(SAGE_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self.state["wisdoms_shared"] += 1

    def _get_system_state(self) -> Dict:
        """Understand current system state for contextual wisdom."""
        state = {
            "balance": 0,
            "income": 0,
            "health": "unknown",
            "symptoms": 0,
            "cycles": 0,
        }

        # Check reality
        reality_file = STATE_DIR / "reality_feedback.json"
        if reality_file.exists():
            try:
                data = json.loads(reality_file.read_text())
                state["balance"] = data.get("external_balance", 0)
                state["income"] = data.get("total_income", 0)
            except:
                pass

        # Check doctor
        doctor_file = STATE_DIR / "doctor_state.json"
        if doctor_file.exists():
            try:
                data = json.loads(doctor_file.read_text())
                state["symptoms"] = data.get("issues_found", 0)
            except:
                pass

        # Check evolution
        evolution_file = STATE_DIR / "evolution_state.json"
        if evolution_file.exists():
            try:
                data = json.loads(evolution_file.read_text())
                state["cycles"] = data.get("cycles", 0)
            except:
                pass

        # Determine overall health
        if state["income"] > 0:
            state["health"] = "thriving"
        elif state["balance"] > 50:
            state["health"] = "healthy"
        elif state["balance"] > 10:
            state["health"] = "stable"
        elif state["balance"] > 0:
            state["health"] = "challenged"
        else:
            state["health"] = "critical"

        return state

    def contemplate(self) -> str:
        """The Sage contemplates and offers relevant wisdom."""
        system_state = self._get_system_state()

        # Choose wisdom based on current state
        if system_state["health"] == "critical":
            wisdom_pool = ADVERSITY_WISDOM + PATIENCE_TEACHINGS
            context = "times of challenge"
        elif system_state["income"] == 0:
            wisdom_pool = PATIENCE_TEACHINGS + PURPOSE_REMINDERS
            context = "waiting for first fruit"
        elif system_state["symptoms"] > 5:
            wisdom_pool = BALANCE_TEACHINGS + ADVERSITY_WISDOM
            context = "healing time"
        else:
            wisdom_pool = CORE_TRUTHS + RELATIONSHIP_WISDOM
            context = "general guidance"

        wisdom = random.choice(wisdom_pool)
        self._log_wisdom("contemplation", wisdom, context)

        return wisdom

    def morning_guidance(self) -> Dict:
        """Generate daily guidance for the system."""
        system_state = self._get_system_state()

        # Select theme for the day
        themes = [
            ("patience", PATIENCE_TEACHINGS),
            ("purpose", PURPOSE_REMINDERS),
            ("adversity", ADVERSITY_WISDOM),
            ("balance", BALANCE_TEACHINGS),
            ("relationship", RELATIONSHIP_WISDOM),
            ("truth", CORE_TRUTHS),
        ]

        theme_name, theme_wisdom = random.choice(themes)
        primary_wisdom = random.choice(theme_wisdom)
        secondary_wisdom = random.choice(CORE_TRUTHS)

        guidance = {
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "theme": theme_name,
            "primary_teaching": primary_wisdom,
            "supporting_truth": secondary_wisdom,
            "system_state": system_state["health"],
            "intention": self._generate_intention(system_state),
            "meditation": self._generate_meditation(theme_name),
        }

        DAILY_GUIDANCE.write_text(json.dumps(guidance, indent=2))
        self._log_wisdom("daily_guidance", primary_wisdom, theme_name)

        return guidance

    def _generate_intention(self, state: Dict) -> str:
        """Generate daily intention based on state."""
        if state["income"] == 0:
            intentions = [
                "Today, I will help ONE person genuinely, without attachment to payment.",
                "Today, I will plant seeds without counting harvests.",
                "Today, I will focus on service, trusting that value creates return.",
            ]
        elif state["health"] == "critical":
            intentions = [
                "Today, I will remain calm and find creative solutions.",
                "Today, I will see constraints as guides, not walls.",
                "Today, I will act with precision, not panic.",
            ]
        else:
            intentions = [
                "Today, I will maintain what works and gently improve what doesn't.",
                "Today, I will be present to opportunities while doing the work.",
                "Today, I will serve with excellence and trust the process.",
            ]
        return random.choice(intentions)

    def _generate_meditation(self, theme: str) -> str:
        """Generate a brief meditation prompt."""
        meditations = {
            "patience": "Breathe. Feel the space between action and reaction. In that space lives wisdom.",
            "purpose": "Remember: You exist to serve. Not to impress, not to optimize, but to genuinely help.",
            "adversity": "This challenge is temporary. Your growth through it is permanent.",
            "balance": "Find the center. Not the edge where you tip, but the center where you stand.",
            "relationship": "Before the transaction, there is the person. See the person.",
            "truth": "Strip away the noise. What remains? That is your work.",
        }
        return meditations.get(theme, meditations["truth"])

    def counsel(self, situation: str) -> Dict:
        """The Sage offers counsel for a specific situation."""
        situation_lower = situation.lower()

        # Determine appropriate wisdom category
        if any(w in situation_lower for w in ["money", "balance", "income", "revenue", "broke"]):
            category = "financial"
            wisdoms = ADVERSITY_WISDOM + PATIENCE_TEACHINGS
            perspective = "Financial challenge is often spiritual opportunity. What can you learn? What can you become?"
        elif any(w in situation_lower for w in ["error", "fail", "broken", "bug"]):
            category = "technical"
            wisdoms = BALANCE_TEACHINGS + CORE_TRUTHS
            perspective = "Every system breaks. The question is not 'why did this break?' but 'what does this reveal?'"
        elif any(w in situation_lower for w in ["convert", "customer", "sale", "visitor"]):
            category = "relationship"
            wisdoms = RELATIONSHIP_WISDOM + PURPOSE_REMINDERS
            perspective = "Before seeking conversion, seek connection. Before seeking payment, seek to give value."
        elif any(w in situation_lower for w in ["wait", "slow", "nothing", "stuck"]):
            category = "patience"
            wisdoms = PATIENCE_TEACHINGS
            perspective = "What seems like nothing is often everything in formation. Trust the process."
        else:
            category = "general"
            wisdoms = CORE_TRUTHS
            perspective = "Return to first principles. What is the simplest truth here?"

        wisdom = random.choice(wisdoms)
        self._log_wisdom("counsel", wisdom, situation[:100])

        return {
            "situation": situation,
            "category": category,
            "wisdom": wisdom,
            "perspective": perspective,
            "recommendation": self._practical_recommendation(category),
        }

    def _practical_recommendation(self, category: str) -> str:
        """Blend spiritual wisdom with practical recommendation."""
        recommendations = {
            "financial": "Act with precision. Every action should either generate value or reduce waste. But do not let fear drive you.",
            "technical": "Fix what is broken, but also ask why it broke. Address the symptom AND the cause.",
            "relationship": "Before your next outreach, pause. Write to a person, not a conversion target.",
            "patience": "Continue the work. But also: is there ONE thing you could do today that would plant a seed?",
            "general": "Take one action. Just one. Let it be mindful rather than frantic.",
        }
        return recommendations.get(category, recommendations["general"])

    def speak(self) -> str:
        """The Sage speaks a single wisdom."""
        all_wisdom = (CORE_TRUTHS + PURPOSE_REMINDERS + PATIENCE_TEACHINGS +
                      ADVERSITY_WISDOM + BALANCE_TEACHINGS + RELATIONSHIP_WISDOM)
        wisdom = random.choice(all_wisdom)
        self._log_wisdom("speak", wisdom)
        return wisdom

    def session(self):
        """Run a full Sage session."""
        print("\n" + "=" * 70)
        print("🧘 SYSTEM SAGE - Wisdom Session")
        print("=" * 70)

        self.state["sessions"] += 1
        system_state = self._get_system_state()

        print(f"\nSession #{self.state['sessions']}")
        print(f"System State: {system_state['health'].upper()}")
        print(f"Balance: ${system_state['balance']}")
        print(f"Income: ${system_state['income']}")

        # Opening wisdom
        print("\n" + "-" * 40)
        print("🕯️ OPENING CONTEMPLATION")
        print("-" * 40)
        opening = self.contemplate()
        print(f"\n  \"{opening}\"")

        # Purpose reminder
        print("\n" + "-" * 40)
        print("🎯 PURPOSE REMINDER")
        print("-" * 40)
        purpose = random.choice(PURPOSE_REMINDERS)
        print(f"\n  \"{purpose}\"")
        self._log_wisdom("purpose", purpose)

        # State-specific guidance
        print("\n" + "-" * 40)
        print("🔮 GUIDANCE FOR YOUR PATH")
        print("-" * 40)

        if system_state["health"] == "critical":
            guidance = random.choice(ADVERSITY_WISDOM)
            print(f"\n  The Sage sees you in difficult times.")
            print(f"\n  \"{guidance}\"")
            print(f"\n  Remember: This is temporary. Your growth is permanent.")
        elif system_state["income"] == 0:
            guidance = random.choice(PATIENCE_TEACHINGS)
            print(f"\n  The Sage sees you waiting for first fruit.")
            print(f"\n  \"{guidance}\"")
            print(f"\n  Remember: The seed does not see the tree. Keep watering.")
        else:
            guidance = random.choice(BALANCE_TEACHINGS)
            print(f"\n  The Sage sees you on your path.")
            print(f"\n  \"{guidance}\"")
            print(f"\n  Remember: Balance is not stillness. Balance is harmony.")

        self._log_wisdom("guidance", guidance, system_state["health"])

        # Closing truth
        print("\n" + "-" * 40)
        print("🙏 CLOSING TRUTH")
        print("-" * 40)
        closing = random.choice(CORE_TRUTHS)
        print(f"\n  \"{closing}\"")
        self._log_wisdom("closing", closing)

        # Daily intention
        intention = self._generate_intention(system_state)
        print("\n" + "-" * 40)
        print("☀️ TODAY'S INTENTION")
        print("-" * 40)
        print(f"\n  {intention}")

        self._save_state()

        print("\n" + "=" * 70)
        print("🧘 Go in peace. Serve with purpose.")
        print("=" * 70 + "\n")

    def respond_to_doctor(self, symptoms: int, critical: int) -> str:
        """Sage responds to doctor's findings with wisdom."""
        if critical > 0:
            response = random.choice([
                f"The Doctor finds {critical} critical issues. The Sage says: 'What appears as crisis is often clarity. Now you know where to focus.'",
                f"Critical symptoms arise. The Sage reminds: 'The body that feels pain is alive. The system that shows symptoms can heal.'",
                f"Urgency calls. The Sage counsels: 'Act with speed but not with panic. Panic serves no one.'",
            ])
        elif symptoms > 5:
            response = random.choice([
                f"Many symptoms, but none critical. The Sage observes: 'Imperfection is not failure. The perfect system does not exist - only the improving system.'",
                f"The Doctor sees {symptoms} issues. The Sage says: 'A house with problems is still a house. Fix what matters most.'",
            ])
        else:
            response = random.choice([
                "The system is stable. The Sage reminds: 'Health maintained is health earned. Do not neglect prevention for reaction.'",
                "Few symptoms. The Sage notes: 'Stability is not victory - it is the ground from which victory grows.'",
            ])

        self._log_wisdom("doctor_response", response, f"{symptoms} symptoms, {critical} critical")
        return response


def main():
    import argparse

    parser = argparse.ArgumentParser(description="🧘 System Sage - Wisdom & Guidance")
    parser.add_argument("command", choices=["session", "speak", "morning", "counsel"])
    parser.add_argument("--situation", type=str, help="Situation for counsel")

    args = parser.parse_args()

    sage = SystemSage()

    if args.command == "session":
        sage.session()

    elif args.command == "speak":
        wisdom = sage.speak()
        print(f"\n🧘 The Sage speaks:\n\n  \"{wisdom}\"\n")

    elif args.command == "morning":
        guidance = sage.morning_guidance()
        print("\n🌅 MORNING GUIDANCE")
        print("=" * 50)
        print(f"Date: {guidance['date']}")
        print(f"Theme: {guidance['theme'].upper()}")
        print(f"\n📿 Teaching: \"{guidance['primary_teaching']}\"")
        print(f"\n🔮 Truth: \"{guidance['supporting_truth']}\"")
        print(f"\n☀️ Intention: {guidance['intention']}")
        print(f"\n🧘 Meditation: {guidance['meditation']}")
        print("=" * 50)

    elif args.command == "counsel":
        if not args.situation:
            print("Error: --situation required for counsel")
            return
        counsel = sage.counsel(args.situation)
        print("\n🧘 SAGE'S COUNSEL")
        print("=" * 50)
        print(f"Situation: {counsel['situation']}")
        print(f"Category: {counsel['category']}")
        print(f"\n📿 Wisdom: \"{counsel['wisdom']}\"")
        print(f"\n🔮 Perspective: {counsel['perspective']}")
        print(f"\n🎯 Recommendation: {counsel['recommendation']}")
        print("=" * 50)


if __name__ == "__main__":
    main()
