#!/usr/bin/env python3
"""
Autonomous Job Application Agent
Runs 24/7, sends applications, monitors responses, follows up
Part of the Hands-Off System autonomous infrastructure
"""

import time
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta
import sys

sys.path.insert(0, str(Path(__file__).parent))

class JobApplicationAgent:
    """Autonomous agent for job applications."""

    def __init__(self):
        self.state_file = Path(__file__).parent.parent / "state" / "job_agent_state.json"
        self.applications_dir = Path(__file__).parent.parent / "applications"
        self.load_state()

    def load_state(self):
        """Load agent state."""
        if self.state_file.exists():
            self.state = json.loads(self.state_file.read_text())
        else:
            self.state = {
                "applications_sent": 0,
                "applications_pending": [],
                "responses_received": 0,
                "interviews_scheduled": 0,
                "last_check": None,
                "last_send": None,
                "queue": [],
                "sent_history": []
            }

    def save_state(self):
        """Save agent state."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state["last_check"] = datetime.now(timezone.utc).isoformat()
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def load_applications_queue(self):
        """Load pending applications from queue."""
        queue_file = self.applications_dir / "queue.json"
        if queue_file.exists():
            return json.loads(queue_file.read_text()).get("applications", [])
        return []

    def should_send_applications(self):
        """Check if it's time to send applications."""
        # Send once per day at most to avoid spam
        if not self.state["last_send"]:
            return True

        last_send = datetime.fromisoformat(self.state["last_send"])
        hours_since = (datetime.now(timezone.utc) - last_send).total_seconds() / 3600
        return hours_since >= 24

    def send_pending_applications(self):
        """Send all pending applications from queue."""
        try:
            from email_sender import HandsOffEmailer
            emailer = HandsOffEmailer()
        except (ImportError, ValueError) as e:
            print(f"Email system not configured: {e}")
            return 0

        queue = self.load_applications_queue()
        if not queue:
            print("No applications in queue")
            return 0

        sent = 0
        for app in queue:
            if app.get("status") == "sent":
                continue

            # Read application body
            body_file = self.applications_dir / app.get("body_file", "")
            if not body_file.exists():
                print(f"Missing body file for {app['company']}")
                continue

            body = body_file.read_text()
            # Remove email headers if present
            if body.startswith("To:"):
                body = '\n'.join(body.split('\n')[2:]).strip()

            # Send application
            success = emailer.send_job_application(
                company=app["company"],
                to=app["to"],
                subject=app["subject"],
                body=body
            )

            if success:
                sent += 1
                app["status"] = "sent"
                app["sent_at"] = datetime.now(timezone.utc).isoformat()
                self.state["sent_history"].append({
                    "company": app["company"],
                    "sent_at": app["sent_at"]
                })

            time.sleep(2)  # Rate limit

        self.state["applications_sent"] += sent
        self.state["last_send"] = datetime.now(timezone.utc).isoformat()
        return sent

    def check_for_responses(self):
        """Check email for application responses."""
        try:
            from email_monitor import EmailMonitor
            monitor = EmailMonitor()
            result = monitor.run_cycle()

            if result.get("interviews"):
                self.state["interviews_scheduled"] += result["interviews"]

            if result.get("new_emails"):
                self.state["responses_received"] += result["new_emails"]

            return result
        except Exception as e:
            print(f"Email monitoring not available: {e}")
            return None

    def schedule_follow_ups(self):
        """Schedule follow-up emails for pending applications."""
        # TODO: Implement follow-up scheduling
        # - Check applications sent 7+ days ago
        # - Send polite follow-up if no response
        # - Track follow-up count
        pass

    def run_cycle(self):
        """Run one agent cycle."""
        print(f"\n{'='*60}")
        print(f"Job Application Agent - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"{'='*60}")

        # Send pending applications if it's time
        if self.should_send_applications():
            print("Checking for applications to send...")
            sent = self.send_pending_applications()
            if sent > 0:
                print(f"✓ Sent {sent} job applications")
        else:
            print("Waiting 24h between application batches")

        # Check for responses
        print("Checking for email responses...")
        response_result = self.check_for_responses()
        if response_result:
            print(f"  New emails: {response_result.get('new_emails', 0)}")
            print(f"  Auto-responses sent: {response_result.get('responses', 0)}")

        # Schedule follow-ups
        # self.schedule_follow_ups()

        # Save state
        self.save_state()

        # Stats
        print(f"\nStats:")
        print(f"  Total sent: {self.state['applications_sent']}")
        print(f"  Responses: {self.state['responses_received']}")
        print(f"  Interviews: {self.state['interviews_scheduled']}")
        print(f"  Last send: {self.state['last_send'] or 'Never'}")

    def run_forever(self):
        """Run agent continuously."""
        print("Starting autonomous job application agent...")
        print("Running 24/7 - Ctrl+C to stop")

        while True:
            try:
                self.run_cycle()
                print(f"\nNext check in 1 hour...")
                time.sleep(3600)  # Check every hour

            except KeyboardInterrupt:
                print("\n\nAgent stopped by user")
                break
            except Exception as e:
                print(f"\n✗ Error in agent cycle: {e}")
                print("Continuing in 5 minutes...")
                time.sleep(300)


def main():
    """Run the job application agent."""
    agent = JobApplicationAgent()

    if "--once" in sys.argv:
        agent.run_cycle()
    else:
        agent.run_forever()


if __name__ == "__main__":
    main()
