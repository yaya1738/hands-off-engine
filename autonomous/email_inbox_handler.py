"""Read-only compatibility facade for legacy email automation.

Inbox access, credential handling, message mutation, GitHub comments, and
income-system side effects are centralized authority operations.
"""
import re


class EmailInboxHandler:
    def __init__(self):
        self.email = None
        self.app_password = None
        self.mail = None
        self.state = {"emails_processed": 0, "actions_taken": [], "emails_archived": 0}

    def load_credentials(self):
        self.email = None
        self.app_password = None
        return False

    def load_state(self):
        return self.state

    def save_state(self):
        return False

    def connect_imap(self):
        return False

    def get_unread_emails(self, folder="INBOX"):
        return []

    def parse_email(self, email_id):
        return None

    def is_bounty_related(self, email_data):
        subject = str(email_data.get("subject", "")).lower()
        body = str(email_data.get("body", "")).lower()
        return any(word in subject or word in body for word in ("bounty", "pull request", "cortex", "review"))

    def extract_pr_number(self, text):
        for pattern in (r"PR #(\d+)", r"pull/(\d+)", r"#(\d+)"):
            match = re.search(pattern, str(text), re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def process_email(self, email_data):
        return {"email_id": email_data.get("id"), "action_taken": "authority_required", "details": []}

    def gh_comment(self, pr_num, body):
        return False

    def _notify_income_engine_job_offer(self, job_details):
        return False

    def mark_as_read(self, email_id):
        return False

    def archive_email(self, email_id):
        return False

    def process_inbox(self):
        raise RuntimeError(
            "[FACTORY-AUTHORITY] legacy email inbox automation is disabled; "
            "submit through FactoryAuthorityGateway"
        )


if __name__ == "__main__":
    raise SystemExit(1)
