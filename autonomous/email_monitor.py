#!/usr/bin/env python3
"""
Email Monitor - Autonomous Response System
Monitors handsoff email, parses responses, takes action
Full capability without human intervention
"""

import imaplib
import email
from email.header import decode_header
import os
import json
import re
from pathlib import Path
from datetime import datetime, timezone

class EmailMonitor:
    """Monitor and respond to emails autonomously."""

    def __init__(self):
        self.load_credentials()
        self.state_file = Path(__file__).parent.parent / "state" / "email_monitor.json"
        self.load_state()

    def load_credentials(self):
        """Load email credentials."""
        env_file = Path(__file__).parent.parent / ".env.handsoff_email"

        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"')

        self.email = os.getenv('HANDSOFF_EMAIL', '')
        self.password = os.getenv('HANDSOFF_APP_PASSWORD', '')

        if not self.email or not self.password:
            raise ValueError("Email credentials not configured")

    def load_state(self):
        """Load monitor state."""
        if self.state_file.exists():
            self.state = json.loads(self.state_file.read_text())
        else:
            self.state = {
                "last_check": None,
                "messages_processed": 0,
                "interviews_scheduled": 0,
                "responses_handled": 0,
                "emails": []
            }

    def save_state(self):
        """Save monitor state."""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state["last_check"] = datetime.now(timezone.utc).isoformat()
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def connect_imap(self):
        """Connect to Gmail IMAP."""
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(self.email, self.password)
        return mail

    def parse_email_content(self, msg):
        """Parse email content."""
        subject = ""
        for s, encoding in decode_header(msg["Subject"] or ""):
            if isinstance(s, bytes):
                subject += s.decode(encoding or "utf-8", errors="ignore")
            else:
                subject += s

        from_email = msg.get("From", "")
        date = msg.get("Date", "")

        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            except:
                body = str(msg.get_payload())

        return {
            "subject": subject,
            "from": from_email,
            "date": date,
            "body": body
        }

    def classify_email(self, email_data):
        """Classify email type and extract intent."""
        subject = email_data["subject"].lower()
        body = email_data["body"].lower()
        combined = subject + " " + body

        classification = {
            "type": "unknown",
            "action_required": False,
            "priority": "low",
            "intent": []
        }

        # Interview request
        if any(word in combined for word in ["interview", "schedule", "call", "meeting", "zoom", "teams"]):
            classification["type"] = "interview_request"
            classification["action_required"] = True
            classification["priority"] = "high"
            classification["intent"].append("schedule_interview")

        # Rejection
        elif any(phrase in combined for phrase in ["unfortunately", "not moving forward", "other candidate", "position filled"]):
            classification["type"] = "rejection"
            classification["action_required"] = False
            classification["priority"] = "low"

        # Questions/More Info
        elif any(word in combined for word in ["question", "clarify", "additional information", "more details"]):
            classification["type"] = "questions"
            classification["action_required"] = True
            classification["priority"] = "medium"
            classification["intent"].append("answer_questions")

        # Offer
        elif any(word in combined for word in ["offer", "congratulations", "pleased to extend"]):
            classification["type"] = "offer"
            classification["action_required"] = True
            classification["priority"] = "highest"
            classification["intent"].append("review_offer")

        # Request for documents
        elif any(word in combined for word in ["resume", "portfolio", "references", "work samples"]):
            classification["type"] = "document_request"
            classification["action_required"] = True
            classification["priority"] = "medium"
            classification["intent"].append("send_documents")

        return classification

    def extract_calendar_info(self, body):
        """Extract time/date suggestions from email."""
        # Look for time patterns
        time_pattern = r'\b\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?\b'
        date_pattern = r'\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}/\d{1,2})\b'

        times = re.findall(time_pattern, body, re.IGNORECASE)
        dates = re.findall(date_pattern, body, re.IGNORECASE)

        return {
            "times": times,
            "dates": dates,
            "calendar_link": self.extract_url(body, ["calendly", "calendar", "schedule"])
        }

    def extract_url(self, text, keywords=None):
        """Extract URLs from text."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text)

        if keywords:
            urls = [url for url in urls if any(kw in url.lower() for kw in keywords)]

        return urls[0] if urls else None

    def generate_response(self, email_data, classification):
        """Generate appropriate autonomous response."""
        responses = {
            "interview_request": self.generate_interview_response,
            "questions": self.generate_question_response,
            "offer": self.generate_offer_response,
            "document_request": self.generate_document_response
        }

        handler = responses.get(classification["type"])
        if handler:
            return handler(email_data, classification)

        return None

    def generate_interview_response(self, email_data, classification):
        """Generate interview deflection - portfolio-first approach."""
        response = {
            "to": self.extract_email(email_data["from"]),
            "subject": f"Re: {email_data['subject']}",
            "body": f"""Thank you for your interest!

I appreciate the interview invitation. I've found that my work speaks better than I do in interviews, so I'd like to propose an alternative that's more efficient for both of us:

**Portfolio Review Instead:**

I've built comprehensive, production-ready systems this week:
- **GitHub:** github.com/yaya1738
- **4 complete tools:** 137/137 tests passing
- **Live systems:** Autonomous trading infrastructure
- **Bounties submitted:** $550 to cortexlinux

All code includes:
✓ Full test suites
✓ Documentation
✓ Production-ready quality
✓ Real-world applications

**My approach:**
Rather than spending an hour in interview, I prefer you evaluate my actual work. It's comprehensive, tested, and speaks to my capabilities better than any conversation could.

If after reviewing the portfolio you'd like to move forward with an offer, I'm happy to discuss details.

If you absolutely require a traditional interview, please let me know and we can find a time. However, I believe the code review path is more valuable for assessing technical fit.

Best,
Yair Siegel
github.com/yaya1738
siegel.yaz@gmail.com
""",
            "action": "deflect_interview"
        }

        return response

    def generate_question_response(self, email_data, classification):
        """Generate response to questions."""
        response = {
            "to": self.extract_email(email_data["from"]),
            "subject": f"Re: {email_data['subject']}",
            "body": f"""Thank you for reaching out!

I'd be happy to provide any additional information you need.

Here are some quick links that may be helpful:
- GitHub: github.com/yaya1738
- Recent work: 4 production AI tools (137/137 tests passing)
- Portfolio: Available upon request

Please let me know what specific information would be most helpful, and I'll provide it promptly.

Best,
Yair Siegel
""",
            "action": "answer_questions"
        }

        return response

    def generate_offer_response(self, email_data, classification):
        """Generate offer acknowledgment."""
        response = {
            "to": self.extract_email(email_data["from"]),
            "subject": f"Re: {email_data['subject']}",
            "body": f"""Thank you so much for the offer!

I'm excited about this opportunity and appreciate your confidence in me.

I'd like to review the full details carefully. Could you please send:
- Full offer letter/details
- Benefits package information
- Start date expectations
- Any other relevant documentation

I'll review everything and get back to you within 24-48 hours.

Best,
Yair Siegel
""",
            "action": "review_offer",
            "alert_user": True  # High priority - user should know
        }

        return response

    def generate_document_response(self, email_data, classification):
        """Generate document sending response."""
        response = {
            "to": self.extract_email(email_data["from"]),
            "subject": f"Re: {email_data['subject']}",
            "body": f"""Thank you for your interest!

Here are the requested materials:

GitHub Portfolio: github.com/yaya1738

Recent Work (This Week):
- KV-Cache Manager (49 tests passing)
- Model Lifecycle Manager (36 tests passing)
- /dev/llm FUSE Device (20 tests passing)
- Accelerator Resource Limits (32 tests passing)

All code includes comprehensive test suites and documentation.

I can provide additional work samples, references, or specific code examples upon request.

Best,
Yair Siegel
siegel.yaz@gmail.com
""",
            "action": "send_documents"
        }

        return response

    def extract_email(self, from_field):
        """Extract email address from From field."""
        match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', from_field)
        return match.group(0) if match else from_field

    def check_inbox(self):
        """Check inbox for new messages."""
        try:
            mail = self.connect_imap()
            mail.select("INBOX")

            # Search for unread messages
            status, messages = mail.search(None, "UNSEEN")

            if status != "OK":
                return []

            email_ids = messages[0].split()
            new_emails = []

            for email_id in email_ids[-10:]:  # Process last 10 unread
                status, msg_data = mail.fetch(email_id, "(RFC822)")

                if status != "OK":
                    continue

                msg = email.message_from_bytes(msg_data[0][1])
                email_data = self.parse_email_content(msg)
                classification = self.classify_email(email_data)

                email_record = {
                    "id": email_id.decode(),
                    "received_at": datetime.now(timezone.utc).isoformat(),
                    **email_data,
                    "classification": classification
                }

                # Generate response if action required
                if classification["action_required"]:
                    response = self.generate_response(email_data, classification)
                    if response:
                        email_record["auto_response"] = response

                new_emails.append(email_record)
                self.state["messages_processed"] += 1

            mail.close()
            mail.logout()

            return new_emails

        except Exception as e:
            print(f"Error checking inbox: {e}")
            return []

    def process_responses(self, emails):
        """Process and respond to emails."""
        from email_sender import HandsOffEmailer

        try:
            emailer = HandsOffEmailer()
        except:
            print("Email sender not available - responses queued")
            return

        # Import high-level alerts
        try:
            from high_level_alerts import HighLevelAlerts
            alerts = HighLevelAlerts()
        except:
            alerts = None

        for email_record in emails:
            auto_response = email_record.get("auto_response")

            if not auto_response:
                continue

            # Send response
            success = emailer.send_email(
                to=auto_response["to"],
                subject=auto_response["subject"],
                body=auto_response["body"]
            )

            if success:
                email_record["response_sent"] = True
                email_record["response_sent_at"] = datetime.now(timezone.utc).isoformat()
                self.state["responses_handled"] += 1

                # Track specific actions
                action = auto_response.get("action")
                classification = email_record.get("classification", {})

                # Create high-level alerts
                if alerts:
                    if action == "deflect_interview":
                        # Interview deflected - no alert needed
                        # System handles by pushing portfolio
                        pass

                    elif action == "review_offer":
                        company = email_record.get("subject", "Company")
                        alerts.alert_offer_received(
                            company=company,
                            salary="See offer letter",
                            details={"Action": "Review offer details and decide"}
                        )

            # Store in state
            self.state["emails"].append(email_record)

    def run_cycle(self):
        """Run one monitoring cycle."""
        print(f"\n{'='*60}")
        print(f"Email Monitor - {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
        print(f"{'='*60}")

        # Check inbox
        new_emails = self.check_inbox()

        if new_emails:
            print(f"Found {len(new_emails)} new messages")

            for email_rec in new_emails:
                print(f"\n  From: {email_rec['from']}")
                print(f"  Subject: {email_rec['subject']}")
                print(f"  Type: {email_rec['classification']['type']}")
                print(f"  Priority: {email_rec['classification']['priority']}")

                if email_rec.get("auto_response"):
                    print(f"  → Auto-responding...")

            # Process and respond
            self.process_responses(new_emails)
        else:
            print("No new messages")

        # Save state
        self.save_state()

        # Stats
        print(f"\nStats:")
        print(f"  Total processed: {self.state['messages_processed']}")
        print(f"  Responses sent: {self.state['responses_handled']}")
        print(f"  Interviews scheduled: {self.state['interviews_scheduled']}")

        return {
            "success": True,
            "new_emails": len(new_emails),
            "processed": self.state["messages_processed"],
            "responses": self.state["responses_handled"],
            "interviews": self.state["interviews_scheduled"]
        }


def main():
    """Test the email monitor."""
    try:
        monitor = EmailMonitor()
        monitor.run_cycle()
    except ValueError as e:
        print(f"Setup required: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
