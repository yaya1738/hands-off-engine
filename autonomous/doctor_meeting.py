#!/usr/bin/env python3
"""
🏥 DOCTOR MEETING - System Health Consultation
Serving: Yair Siegel

The doctor presents findings to the war room. Executives and analysts
respond with questions, preparations, and action items.

Meeting format:
1. Doctor presents examination findings
2. Each executive responds based on their domain
3. Analysts provide additional analysis
4. Action items are generated
5. Meeting minutes logged
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_DIR = BASE_DIR / "state"

# Meeting output
MEETING_LOG = STATE_DIR / "doctor_meetings.jsonl"
ACTION_ITEMS = STATE_DIR / "meeting_actions.json"

# Import executives and analysts
EXECUTIVES = {
    "ceo": {
        "name": "CEO",
        "emoji": "👔",
        "domain": "mission",
        "responds_to": ["critical", "income", "runway"],
        "responses": [
            "This is a mission-critical finding. We need to act NOW.",
            "How does this affect our core objective of serving Yair Siegel?",
            "I'm escalating this to highest priority.",
            "We cannot let this slide. What's the fastest fix?",
        ]
    },
    "cfo": {
        "name": "CFO",
        "emoji": "💰",
        "domain": "finance",
        "responds_to": ["finance", "wallet", "runway", "balance"],
        "responses": [
            "The financial implications are severe. We have ${balance:.2f} runway.",
            "At this burn rate, we need income within days, not weeks.",
            "I'm preparing emergency financial contingencies.",
            "Every dollar counts. What's the ROI on fixing this?",
        ]
    },
    "cto": {
        "name": "CTO",
        "emoji": "⚙️",
        "domain": "technical",
        "responds_to": ["process", "actuator", "api", "database", "memory", "disk"],
        "responses": [
            "I'll have engineering on this immediately.",
            "This is a technical debt we've been accumulating.",
            "System health is non-negotiable. Preparing fix.",
            "I'm drafting an automated treatment for this class of issues.",
        ]
    },
    "coo": {
        "name": "COO",
        "emoji": "📋",
        "domain": "operations",
        "responds_to": ["outreach", "conversion", "endpoint", "cron"],
        "responses": [
            "Operations will adjust processes to address this.",
            "I'm updating the execution playbook.",
            "We need better monitoring before this happens again.",
            "This affects our delivery capability. Prioritizing fix.",
        ]
    },
    "cso": {
        "name": "CSO",
        "emoji": "🔒",
        "domain": "security",
        "responds_to": ["security", "secret", "exposure", "credential"],
        "responses": [
            "SECURITY ALERT. This requires immediate remediation.",
            "I'm initiating credential rotation protocol.",
            "We cannot have secrets exposed. Locking this down now.",
            "Security posture compromised. Emergency response activated.",
        ]
    },
}

ANALYSTS = {
    "risk": {
        "name": "Risk Analyst",
        "emoji": "⚠️",
        "analyzes": ["critical", "warning"],
        "responses": [
            "Risk level: {severity}. Probability of escalation: HIGH.",
            "This symptom pattern indicates systemic issues.",
            "Recommending immediate mitigation measures.",
            "Adding to risk register with priority 1.",
        ]
    },
    "ops": {
        "name": "Ops Analyst",
        "emoji": "📊",
        "analyzes": ["info", "warning"],
        "responses": [
            "Tracking this in operational metrics.",
            "Historical trend shows this is {trend}.",
            "Operational impact assessment: MEDIUM to HIGH.",
            "Preparing dashboard alert for continuous monitoring.",
        ]
    },
}


class DoctorMeeting:
    """
    🏥 Conducts health consultation meeting with the war room.
    """

    def __init__(self):
        self.meeting_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self.minutes = []
        self.action_items = []
        self.attendees = []

    def _log(self, speaker: str, content: str, category: str = "statement"):
        """Log meeting minutes."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meeting_id": self.meeting_id,
            "speaker": speaker,
            "category": category,
            "content": content,
        }
        self.minutes.append(entry)
        print(f"  {speaker}: {content}")

    def _save_meeting(self):
        """Save meeting to log."""
        for entry in self.minutes:
            with open(MEETING_LOG, "a") as f:
                f.write(json.dumps(entry) + "\n")

        # Save action items
        actions = self._load_actions()
        actions["meetings"].append({
            "meeting_id": self.meeting_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "items": self.action_items,
        })
        actions["last_updated"] = datetime.now(timezone.utc).isoformat()
        ACTION_ITEMS.write_text(json.dumps(actions, indent=2))

    def _load_actions(self) -> Dict:
        if ACTION_ITEMS.exists():
            return json.loads(ACTION_ITEMS.read_text())
        return {"meetings": [], "last_updated": None}

    def conduct_meeting(self):
        """Run the full doctor consultation meeting."""
        print("\n" + "=" * 70)
        print("🏥 DOCTOR CONSULTATION MEETING")
        print("=" * 70)
        print(f"Meeting ID: {self.meeting_id}")
        print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        print("-" * 70)

        # Import and run doctor examination
        from autonomous.health_diagnostics import HealthDiagnostics

        doctor = HealthDiagnostics()
        self._log("📋 Secretary", "Meeting called to order. Doctor has requested consultation.")

        # Roll call
        print("\n📋 ROLL CALL")
        print("-" * 40)
        self.attendees = list(EXECUTIVES.keys()) + list(ANALYSTS.keys()) + ["doctor"]
        for exec_id, exec_data in EXECUTIVES.items():
            print(f"  {exec_data['emoji']} {exec_data['name']} - Present")
        for analyst_id, analyst_data in ANALYSTS.items():
            print(f"  {analyst_data['emoji']} {analyst_data['name']} - Present")
        print("  🩺 System Doctor - Presenting")

        # Doctor presents findings
        print("\n🩺 DOCTOR'S PRESENTATION")
        print("-" * 40)
        self._log("🩺 Doctor", "Beginning system health examination...")

        symptoms = doctor.full_examination()

        print("\n")
        self._log("🩺 Doctor", f"Examination complete. Found {len(symptoms)} symptoms.")

        # Get sensitive data
        sensitive = doctor.get_sensitive_summary()
        self._log("🩺 Doctor", f"Sensitive data: Wallet ${sensitive.get('wallet_usdc', 'unknown')}, " +
                  f"Credentials: OpenAI={sensitive.get('credentials', {}).get('openai', False)}, " +
                  f"Telegram={sensitive.get('credentials', {}).get('telegram', False)}, " +
                  f"Polymarket={sensitive.get('credentials', {}).get('polymarket', False)}")

        # Diagnose
        diagnoses = doctor.diagnose()
        self._log("🩺 Doctor", f"Diagnosed {len(diagnoses)} root causes.")

        for d in diagnoses:
            self._log("🩺 Doctor", f"DIAGNOSIS: {d.root_cause} (Priority {d.priority})")

        # Executive responses
        print("\n👔 EXECUTIVE RESPONSES")
        print("-" * 40)

        for symptom in symptoms:
            component = symptom.component.lower()
            severity = symptom.severity

            # Find responding executives
            for exec_id, exec_data in EXECUTIVES.items():
                if any(keyword in component for keyword in exec_data["responds_to"]):
                    import random
                    response = random.choice(exec_data["responses"])
                    # Fill in variables if present
                    if "{balance" in response:
                        response = response.format(balance=sensitive.get("wallet_usdc", 0))
                    self._log(
                        f"{exec_data['emoji']} {exec_data['name']}",
                        f"RE: {symptom.symptom} - {response}",
                        "response"
                    )

                    # Generate action item
                    if severity == "critical":
                        self.action_items.append({
                            "owner": exec_data["name"],
                            "priority": "HIGH",
                            "item": f"Address: {symptom.symptom}",
                            "due": "IMMEDIATE",
                        })
                    break

        # Analyst responses
        print("\n📊 ANALYST ANALYSIS")
        print("-" * 40)

        critical_count = len([s for s in symptoms if s.severity == "critical"])
        warning_count = len([s for s in symptoms if s.severity == "warning"])

        for analyst_id, analyst_data in ANALYSTS.items():
            import random
            response = random.choice(analyst_data["responses"])
            response = response.format(
                severity="CRITICAL" if critical_count > 0 else "WARNING",
                trend="worsening" if critical_count > 2 else "stable"
            )
            self._log(
                f"{analyst_data['emoji']} {analyst_data['name']}",
                response,
                "analysis"
            )

        # Prescriptions
        print("\n💊 DOCTOR'S PRESCRIPTIONS")
        print("-" * 40)

        treatments = doctor.prescribe()
        for t in treatments:
            self._log("🩺 Doctor", f"PRESCRIBE: {t.treatment}")
            self.action_items.append({
                "owner": "Doctor",
                "priority": "HIGH",
                "item": t.treatment,
                "command": t.command if t.command else None,
            })

        # Summary and action items
        print("\n📋 ACTION ITEMS")
        print("-" * 40)

        for i, item in enumerate(self.action_items, 1):
            print(f"  {i}. [{item['priority']}] {item['owner']}: {item['item']}")

        # Closing
        print("\n" + "-" * 40)
        self._log("📋 Secretary", f"Meeting adjourned. {len(self.action_items)} action items recorded.")

        # Save
        self._save_meeting()

        print(f"\n📝 Minutes saved to: {MEETING_LOG}")
        print(f"📋 Actions saved to: {ACTION_ITEMS}")
        print("=" * 70)

        return {
            "meeting_id": self.meeting_id,
            "symptoms": len(symptoms),
            "diagnoses": len(diagnoses),
            "action_items": len(self.action_items),
            "critical": critical_count,
            "warnings": warning_count,
        }

    def quick_briefing(self):
        """Quick health briefing without full meeting."""
        from autonomous.health_diagnostics import HealthDiagnostics

        doctor = HealthDiagnostics()

        print("\n🏥 QUICK HEALTH BRIEFING")
        print("=" * 50)

        # Quick exam
        symptoms = doctor.full_examination()
        sensitive = doctor.get_sensitive_summary()

        print(f"\n📊 STATUS SUMMARY:")
        print(f"  Wallet: ${sensitive.get('wallet_usdc', 'unknown')}")
        print(f"  Critical Issues: {len([s for s in symptoms if s.severity == 'critical'])}")
        print(f"  Warnings: {len([s for s in symptoms if s.severity == 'warning'])}")
        print(f"  Credentials: OpenAI={'✓' if sensitive.get('credentials', {}).get('openai') else '✗'} " +
              f"Telegram={'✓' if sensitive.get('credentials', {}).get('telegram') else '✗'} " +
              f"Polymarket={'✓' if sensitive.get('credentials', {}).get('polymarket') else '✗'}")

        return symptoms


def main():
    import argparse

    parser = argparse.ArgumentParser(description="🏥 Doctor Consultation Meeting")
    parser.add_argument("command", choices=["meeting", "briefing", "actions"])

    args = parser.parse_args()

    meeting = DoctorMeeting()

    if args.command == "meeting":
        meeting.conduct_meeting()

    elif args.command == "briefing":
        meeting.quick_briefing()

    elif args.command == "actions":
        actions = meeting._load_actions()
        print("\n📋 PENDING ACTION ITEMS")
        print("=" * 50)
        if actions.get("meetings"):
            latest = actions["meetings"][-1]
            print(f"From meeting: {latest['meeting_id']}")
            for i, item in enumerate(latest.get("items", []), 1):
                print(f"  {i}. [{item['priority']}] {item['owner']}: {item['item']}")
        else:
            print("  No action items recorded.")


if __name__ == "__main__":
    main()
