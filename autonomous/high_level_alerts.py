#!/usr/bin/env python3
"""
High-Level Alerts - Only Important Stuff
Yair only sees: interviews scheduled, offers, critical decisions
Everything else handled autonomously
"""

import json
from pathlib import Path
from datetime import datetime, timezone

class HighLevelAlerts:
    """Alert system for high-level events only."""

    def __init__(self):
        self.alerts_file = Path(__file__).parent.parent / "state" / "high_level_alerts.json"
        self.load_alerts()

    def load_alerts(self):
        """Load alerts."""
        if self.alerts_file.exists():
            self.alerts = json.loads(self.alerts_file.read_text())
        else:
            self.alerts = {
                "pending": [],
                "dismissed": [],
                "alert_count": 0
            }

    def save_alerts(self):
        """Save alerts."""
        self.alerts_file.parent.mkdir(parents=True, exist_ok=True)
        self.alerts_file.write_text(json.dumps(self.alerts, indent=2))

    def add_alert(self, alert_type: str, title: str, details: dict, priority: str = "high"):
        """
        Add high-level alert.

        Alert types:
        - interview_scheduled: Interview confirmed
        - offer_received: Job offer received
        - urgent_decision: Needs decision within 24h
        - high_value: Opportunity >$200k
        """
        alert = {
            "id": self.alerts["alert_count"],
            "type": alert_type,
            "title": title,
            "details": details,
            "priority": priority,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending"
        }

        self.alerts["pending"].append(alert)
        self.alerts["alert_count"] += 1
        self.save_alerts()

        # Print to console
        print(f"\n{'='*60}")
        print(f"🚨 HIGH-LEVEL ALERT: {title}")
        print(f"{'='*60}")
        print(f"Type: {alert_type}")
        print(f"Priority: {priority}")
        for key, value in details.items():
            print(f"{key}: {value}")
        print(f"{'='*60}\n")

        return alert["id"]

    def get_pending_alerts(self):
        """Get all pending alerts."""
        return [a for a in self.alerts["pending"] if a["status"] == "pending"]

    def dismiss_alert(self, alert_id: int):
        """Dismiss an alert."""
        for alert in self.alerts["pending"]:
            if alert["id"] == alert_id:
                alert["status"] = "dismissed"
                alert["dismissed_at"] = datetime.now(timezone.utc).isoformat()
                self.alerts["dismissed"].append(alert)
                self.alerts["pending"].remove(alert)
                self.save_alerts()
                return True
        return False

    def alert_interview_scheduled(self, company: str, date: str, time: str, link: str = None):
        """Alert: Interview scheduled."""
        details = {
            "Company": company,
            "Date": date,
            "Time": time,
            "Action": "Show up and interview"
        }
        if link:
            details["Link"] = link

        return self.add_alert(
            alert_type="interview_scheduled",
            title=f"Interview Scheduled: {company}",
            details=details,
            priority="high"
        )

    def alert_offer_received(self, company: str, salary: str, details: dict = None):
        """Alert: Offer received."""
        alert_details = {
            "Company": company,
            "Salary": salary,
            "Action": "Review offer details and decide"
        }
        if details:
            alert_details.update(details)

        return self.add_alert(
            alert_type="offer_received",
            title=f"JOB OFFER: {company} - {salary}",
            details=alert_details,
            priority="highest"
        )

    def alert_urgent_decision(self, title: str, deadline: str, details: dict):
        """Alert: Urgent decision needed."""
        alert_details = {
            "Deadline": deadline,
            **details
        }

        return self.add_alert(
            alert_type="urgent_decision",
            title=title,
            details=alert_details,
            priority="urgent"
        )

    def alert_high_value(self, title: str, value: str, details: dict):
        """Alert: High-value opportunity."""
        alert_details = {
            "Value": value,
            **details
        }

        return self.add_alert(
            alert_type="high_value",
            title=title,
            details=alert_details,
            priority="high"
        )

    def get_summary(self):
        """Get alert summary for display."""
        pending = self.get_pending_alerts()

        if not pending:
            return "No pending high-level items. System handling everything."

        summary = f"\n{'='*60}\n"
        summary += f"HIGH-LEVEL ALERTS ({len(pending)} pending)\n"
        summary += f"{'='*60}\n\n"

        for alert in pending:
            summary += f"[{alert['priority'].upper()}] {alert['title']}\n"
            for key, value in alert['details'].items():
                summary += f"  {key}: {value}\n"
            summary += "\n"

        return summary


def main():
    """Test alerts."""
    alerts = HighLevelAlerts()

    # Example: Interview scheduled
    alerts.alert_interview_scheduled(
        company="Pydantic",
        date="2025-12-10",
        time="2:00 PM ET",
        link="https://zoom.us/j/123456"
    )

    # Example: Offer received
    alerts.alert_offer_received(
        company="DuckDuckGo",
        salary="$178,500 + equity",
        details={
            "Benefits": "Full package",
            "Start Date": "2025-01-15",
            "Remote": "Yes"
        }
    )

    # Show summary
    print(alerts.get_summary())


if __name__ == "__main__":
    main()
