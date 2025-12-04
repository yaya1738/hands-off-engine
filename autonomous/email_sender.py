#!/usr/bin/env python3
"""
Hands-Off Email Sender
Autonomous email sending for job applications and communications
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime, timezone
import json

class HandsOffEmailer:
    """Autonomous email sender for hands-off system."""

    def __init__(self):
        self.load_credentials()
        self.state_file = Path(__file__).parent.parent / "state" / "email_state.json"
        self.load_state()

    def load_credentials(self):
        """Load email credentials from environment."""
        env_file = Path(__file__).parent.parent / ".env.handsoff_email"

        if env_file.exists():
            # Parse .env file
            for line in env_file.read_text().splitlines():
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"')

        self.email = os.getenv('HANDSOFF_EMAIL', '')
        self.app_password = os.getenv('HANDSOFF_APP_PASSWORD', '')

        if not self.email or not self.app_password:
            raise ValueError(
                "Email credentials not configured. "
                "Please set HANDSOFF_EMAIL and HANDSOFF_APP_PASSWORD in .env.handsoff_email"
            )

    def load_state(self):
        """Load email sending state."""
        if self.state_file.exists():
            self.state = json.loads(self.state_file.read_text())
        else:
            self.state = {
                "emails_sent": 0,
                "last_sent": None,
                "sent_to": []
            }

    def save_state(self):
        """Save email sending state."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def send_email(self, to: str, subject: str, body: str, reply_to: str = None) -> bool:
        """
        Send email via Gmail SMTP.

        Args:
            to: Recipient email
            subject: Email subject
            body: Email body (plain text)
            reply_to: Optional reply-to address

        Returns:
            bool: True if sent successfully
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = to
            msg['Subject'] = subject
            if reply_to:
                msg['Reply-To'] = reply_to

            msg.attach(MIMEText(body, 'plain'))

            # Connect to Gmail SMTP
            print(f"Sending email to {to}...")
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(self.email, self.app_password)
            server.send_message(msg)
            server.quit()

            # Update state
            self.state['emails_sent'] += 1
            self.state['last_sent'] = datetime.now(timezone.utc).isoformat()
            self.state['sent_to'].append({
                "to": to,
                "subject": subject,
                "sent_at": self.state['last_sent']
            })
            self.save_state()

            print(f"✓ Email sent to {to}")
            return True

        except Exception as e:
            print(f"✗ Failed to send email to {to}: {e}")
            return False

    def send_job_application(self, company: str, to: str, subject: str, body: str) -> bool:
        """Send job application email."""
        print(f"\n{'='*60}")
        print(f"Sending application to {company}")
        print(f"{'='*60}\n")

        success = self.send_email(
            to=to,
            subject=subject,
            body=body,
            reply_to="siegel.yaz@gmail.com"  # Personal email for replies
        )

        if success:
            print(f"✓ {company} application sent successfully!")
        else:
            print(f"✗ {company} application failed")

        return success

    def get_stats(self):
        """Get email sending statistics."""
        return {
            "total_sent": self.state['emails_sent'],
            "last_sent": self.state['last_sent'],
            "recipients": len(self.state['sent_to'])
        }


def main():
    """Test the email sender."""
    try:
        emailer = HandsOffEmailer()
        stats = emailer.get_stats()
        print(f"Email system ready!")
        print(f"Total emails sent: {stats['total_sent']}")
        print(f"Last sent: {stats['last_sent'] or 'Never'}")

    except ValueError as e:
        print(f"Setup required: {e}")
        print("\nSteps:")
        print("1. Create Gmail account for hands-off system")
        print("2. Enable 2FA")
        print("3. Generate App Password")
        print("4. Add to .env.handsoff_email")


if __name__ == "__main__":
    main()
