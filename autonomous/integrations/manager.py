"""
Hands-Off Integration Manager
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

from autonomous.integrations.providers.gmail_oauth import GmailOAuth


class IntegrationManager:

    def __init__(self):
        self.root = Path(__file__).resolve().parent.parent.parent

        self.env_files = [
            self.root / ".env.handsoff_email",
            self.root / ".env",
        ]

        for env_file in self.env_files:
            if env_file.exists():
                load_dotenv(env_file)

    def status(self):
        return {
            "gmail": self.gmail_status(),
        }

    def gmail_status(self):
        email = os.getenv("HANDSOFF_EMAIL")
        password = os.getenv("HANDSOFF_APP_PASSWORD")

        placeholder = (
            not password
            or "YOUR_" in password
            or "PASTE_" in password
            or "HERE" in password
        )

        oauth = GmailOAuth().status()

        return {
            "legacy_app_password": {
                "configured": bool(email and password and not placeholder),
                "email": email or None,
                "password_present": bool(password),
                "password_valid_format": not placeholder,
            },
            "oauth": oauth,
        }


def main():
    manager = IntegrationManager()
    print(json.dumps(manager.status(), indent=2))


if __name__ == "__main__":
    main()
