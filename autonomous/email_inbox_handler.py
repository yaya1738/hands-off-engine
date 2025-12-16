#!/usr/bin/env python3
"""
Email Inbox Handler - Zero-Touch Email Management

Monitors Gmail inbox, processes ALL bounty/PR/GitHub emails automatically.
You NEVER need to check email manually - system handles everything.

Requirements:
- Gmail account
- App password (not regular password)
- IMAP enabled
"""

import imaplib
import email
from email.header import decode_header
import os
import re
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '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')
STATE_FILE = Path(__file__).parent.parent / 'state' / 'email_handler.json'


class EmailInboxHandler:
    """Zero-touch email management for bounty/PR notifications."""

    def __init__(self):
        self.load_credentials()
        self.load_state()
        self.mail = None

    def load_credentials(self):
        """Load Gmail credentials."""
        env_file = Path(__file__).parent.parent / ".env.handsoff_email"

        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"')

        self.email = os.getenv('HANDSOFF_EMAIL', 'siegel.yaz@gmail.com')
        self.app_password = os.getenv('HANDSOFF_APP_PASSWORD', '')

        print(f"Email configured: {self.email}")

    def load_state(self):
        """Load processing state."""
        if STATE_FILE.exists():
            self.state = json.loads(STATE_FILE.read_text())
        else:
            self.state = {
                'emails_processed': 0,
                'last_check': None,
                'processed_ids': [],
                'actions_taken': [],
                'emails_archived': 0
            }

    def save_state(self):
        """Save processing state."""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    def connect_imap(self) -> bool:
        """Connect to Gmail via IMAP."""
        try:
            if not self.app_password:
                print("⚠️  Gmail app password not configured")
                print("    Set HANDSOFF_APP_PASSWORD in .env.handsoff_email")
                return False

            print(f"Connecting to Gmail as {self.email}...")
            self.mail = imaplib.IMAP4_SSL('imap.gmail.com')
            self.mail.login(self.email, self.app_password)
            print("✓ Connected to Gmail")
            return True

        except Exception as e:
            print(f"✗ Failed to connect: {e}")
            return False

    def get_unread_emails(self, folder='INBOX') -> List[bytes]:
        """Get all unread emails."""
        if not self.mail:
            return []

        self.mail.select(folder)

        # Search for unread emails
        status, messages = self.mail.search(None, 'UNSEEN')

        if status != 'OK':
            return []

        email_ids = messages[0].split()
        return email_ids

    def parse_email(self, email_id: bytes) -> Optional[Dict]:
        """Parse email and extract relevant info."""
        try:
            status, msg_data = self.mail.fetch(email_id, '(RFC822)')

            if status != 'OK':
                return None

            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)

            # Decode subject
            subject = email_message['Subject']
            if subject:
                decoded = decode_header(subject)
                subject = decoded[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()

            # Get sender
            from_addr = email_message['From']

            # Get body
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_message.get_payload(decode=True).decode()

            return {
                'id': email_id.decode(),
                'subject': subject,
                'from': from_addr,
                'body': body,
                'date': email_message['Date']
            }

        except Exception as e:
            print(f"Error parsing email: {e}")
            return None

    def is_bounty_related(self, email_data: Dict) -> bool:
        """Check if email is about our bounties/PRs."""
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body', '').lower()
        from_addr = email_data.get('from', '').lower()

        # Keywords that indicate bounty/PR related
        keywords = [
            'cortex', 'cortexlinux',
            'pull request', 'pr #239', 'pr #240', 'pr #241',
            'bounty', 'issue #223', 'issue #222', 'issue #117',
            'coderabbit', 'sonarqube',
            'review', 'merged', 'approved',
            'comment', 'mentioned you'
        ]

        return any(kw in subject or kw in body or kw in from_addr for kw in keywords)

    def extract_pr_number(self, text: str) -> Optional[int]:
        """Extract PR number from text."""
        # Look for patterns like "PR #123", "#123", "pull/123"
        patterns = [
            r'PR #(\d+)',
            r'pull/(\d+)',
            r'#(\d+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))

        return None

    def process_email(self, email_data: Dict) -> Dict:
        """Process email and take action."""
        action = {
            'email_id': email_data['id'],
            'subject': email_data['subject'],
            'action_taken': 'none',
            'details': []
        }

        subject = email_data['subject']
        body = email_data['body']

        # Extract PR number
        pr_num = self.extract_pr_number(subject) or self.extract_pr_number(body)

        # INTEGRAFIX: Detect job offers and notify income_engine
        if self._is_job_offer_email(subject, body):
            action['action_taken'] = 'job_offer_detected'
            job_details = self._extract_job_details(subject, body, email_data.get('from', ''))
            action['details'].append(f"Job offer: {job_details.get('title', 'Unknown')}")
            self._notify_income_engine_job_offer(job_details)

        # Determine action based on email content
        elif 'merged' in subject.lower():
            action['action_taken'] = 'pr_merged'
            action['details'].append(f"PR #{pr_num} merged! Bounty claimable.")
            self.handle_pr_merged(pr_num)

        elif 'approved' in subject.lower() or 'lgtm' in body.lower():
            action['action_taken'] = 'pr_approved'
            action['details'].append(f"PR #{pr_num} approved")
            self.handle_pr_approved(pr_num)

        elif 'changes requested' in subject.lower() or 'requested changes' in body.lower():
            action['action_taken'] = 'changes_requested'
            action['details'].append(f"PR #{pr_num} needs changes")
            self.handle_changes_requested(pr_num, body)

        elif 'commented' in subject.lower() or 'comment' in subject.lower():
            action['action_taken'] = 'new_comment'
            action['details'].append(f"PR #{pr_num} has new comment")
            self.handle_new_comment(pr_num, body)

        elif 'review' in subject.lower():
            action['action_taken'] = 'review_received'
            action['details'].append(f"PR #{pr_num} reviewed")
            self.handle_review(pr_num, body)

        else:
            action['action_taken'] = 'monitored'
            action['details'].append("Email monitored, no action needed")

        return action

    def handle_pr_merged(self, pr_num: Optional[int]):
        """Handle PR merged notification."""
        if not pr_num:
            return

        print(f"\n🎉 PR #{pr_num} MERGED! Bounty is claimable!")

        # Post celebration comment
        bounty_map = {239: 125, 240: 100, 241: 25}
        bounty = bounty_map.get(pr_num, 0)

        if bounty:
            self.gh_comment(pr_num, f"""🎉 Thank you for merging!

Bounty claim in progress for ${bounty}.

This was a pleasure to contribute to Cortex Linux!""")

    def handle_pr_approved(self, pr_num: Optional[int]):
        """Handle PR approval."""
        if not pr_num:
            return

        print(f"✓ PR #{pr_num} approved")
        self.gh_comment(pr_num, "Thank you for the approval! Ready to merge.")

    def handle_changes_requested(self, pr_num: Optional[int], body: str):
        """Handle change requests."""
        if not pr_num:
            return

        print(f"⚠️  PR #{pr_num} needs changes")
        self.gh_comment(pr_num, """Thank you for the feedback!

I'll address the requested changes and push updates shortly.

Please let me know if you need any clarifications.""")

    def handle_new_comment(self, pr_num: Optional[int], body: str):
        """Handle new comments."""
        if not pr_num:
            return

        print(f"💬 PR #{pr_num} has new comment")
        # Check if it needs a response (handled by pr_email_bridge.py)

    def handle_review(self, pr_num: Optional[int], body: str):
        """Handle review notifications."""
        if not pr_num:
            return

        print(f"👀 PR #{pr_num} reviewed")

    def _is_job_offer_email(self, subject: str, body: str) -> bool:
        """INTEGRAFIX: Detect if email is a job offer or work acceptance."""
        subject_lower = subject.lower()
        body_lower = body.lower()

        job_keywords = [
            'job offer', 'offer letter', 'hired', 'welcome to the team',
            'accepted your proposal', 'you\'re hired', 'start date',
            'contract attached', 'congratulations', 'pleased to offer',
            'upwork contract', 'fiverr order', 'freelancer contract',
            'bounty accepted', 'work approved'
        ]

        return any(kw in subject_lower or kw in body_lower for kw in job_keywords)

    def _extract_job_details(self, subject: str, body: str, from_email: str) -> Dict:
        """INTEGRAFIX: Extract job offer details from email."""
        # Extract rate/amount using regex
        rate = 0.0
        rate_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|dollars)',
            r'rate[:\s]+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)'
        ]

        for pattern in rate_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                rate_str = match.group(1).replace(',', '')
                rate = float(rate_str)
                break

        # Determine source
        source = "email"
        if 'upwork' in from_email.lower() or 'upwork' in subject.lower():
            source = "upwork"
        elif 'fiverr' in from_email.lower() or 'fiverr' in subject.lower():
            source = "fiverr"
        elif 'freelancer' in from_email.lower():
            source = "freelancer"
        elif 'github' in from_email.lower() or 'bounty' in subject.lower():
            source = "github_bounty"

        return {
            "title": subject[:100],
            "source": source,
            "rate": rate,
            "details": body[:500],
            "sender_email": from_email
        }

    def _notify_income_engine_job_offer(self, job_details: Dict):
        """INTEGRAFIX: Notify income_engine of job offer."""
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from integrafix.income_engine import IncomeEngine

            engine = IncomeEngine()
            result = engine.record_job_offer_from_email(
                source=job_details['source'],
                title=job_details['title'],
                rate=job_details['rate'],
                details=job_details['details'],
                sender_email=job_details['sender_email']
            )

            print(f"✓ Income engine notified: {result.get('status')}")
            if 'work_id' in result:
                print(f"✓ Work tracking auto-started: {result['work_id']}")

        except Exception as e:
            print(f"Failed to notify income_engine: {e}")

    def gh_comment(self, pr_num: int, body: str):
        """Post comment to GitHub PR."""
        repo = 'cortexlinux/cortex'
        cmd = [
            'gh', 'pr', 'comment', str(pr_num),
            '--repo', repo,
            '--body', body
        ]
        env = os.environ.copy()
        env['GITHUB_TOKEN'] = GITHUB_TOKEN

        try:
            subprocess.run(cmd, capture_output=True, text=True, env=env, check=True)
            print(f"  ✓ Responded via GitHub")
        except:
            pass

    def mark_as_read(self, email_id: bytes):
        """Mark email as read."""
        try:
            self.mail.store(email_id, '+FLAGS', '\\Seen')
        except:
            pass

    def archive_email(self, email_id: bytes):
        """Archive email (move to All Mail, remove from Inbox)."""
        try:
            self.mail.store(email_id, '+X-GM-LABELS', '\\Archive')
            self.state['emails_archived'] += 1
        except:
            pass

    def process_inbox(self):
        """Process all unread emails in inbox."""
        if not self.connect_imap():
            return

        print(f"\n{'='*60}")
        print(f"Processing Gmail Inbox: {self.email}")
        print(f"{'='*60}\n")

        email_ids = self.get_unread_emails()

        if not email_ids:
            print("✓ Inbox clear - no unread emails")
            return

        print(f"Found {len(email_ids)} unread emails\n")

        processed = 0
        bounty_related = 0

        for email_id in email_ids:
            email_data = self.parse_email(email_id)

            if not email_data:
                continue

            print(f"📧 {email_data['subject'][:60]}...")

            # Check if bounty-related
            if self.is_bounty_related(email_data):
                bounty_related += 1
                print(f"   → BOUNTY RELATED")

                # Process and take action
                action = self.process_email(email_data)

                print(f"   → Action: {action['action_taken']}")
                for detail in action['details']:
                    print(f"      {detail}")

                self.state['actions_taken'].append({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    **action
                })

                # Archive bounty emails
                self.archive_email(email_id)
                print(f"   → Archived")

            else:
                print(f"   → Not bounty-related, skipping")

            # Mark as read regardless
            self.mark_as_read(email_id)
            processed += 1
            self.state['emails_processed'] += 1

        self.state['last_check'] = datetime.now(timezone.utc).isoformat()
        self.state['processed_ids'].extend([eid.decode() for eid in email_ids])
        self.save_state()

        print(f"\n{'='*60}")
        print(f"Processed: {processed} emails")
        print(f"Bounty-related: {bounty_related}")
        print(f"Archived: {bounty_related}")
        print(f"Total processed: {self.state['emails_processed']}")
        print(f"{'='*60}\n")

        if self.mail:
            self.mail.close()
            self.mail.logout()

    def continuous_monitoring(self, interval: int = 300):
        """Continuously monitor and process inbox."""
        import time

        print(f"Starting continuous inbox monitoring (every {interval}s)")
        print(f"You NEVER need to check Gmail manually\n")

        while True:
            try:
                self.process_inbox()
            except Exception as e:
                print(f"Error processing inbox: {e}")

            print(f"Next check in {interval}s...")
            time.sleep(interval)


def main():
    """Run email inbox handler."""
    import sys

    handler = EmailInboxHandler()

    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        handler.continuous_monitoring()
    else:
        # One-time inbox processing
        handler.process_inbox()


if __name__ == '__main__':
    main()
