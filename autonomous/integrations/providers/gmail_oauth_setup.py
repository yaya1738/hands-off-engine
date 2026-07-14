"""
Gmail OAuth one-time setup.
Stores Gmail token in Hands-Off vault.
"""

from pathlib import Path
import json

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from autonomous.integrations.vault import CredentialVault


SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]

BASE = Path(__file__).parent.parent.parent.parent
CREDS_FILE = BASE / "credentials.json"
TOKEN_FILE = BASE / "data" / "secrets" / "gmail_token.json"


def main():

    if not CREDS_FILE.exists():
        print("ERROR: credentials.json missing")
        print(f"Place it here: {CREDS_FILE}")
        return

    creds = None

    if TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(
            TOKEN_FILE,
            SCOPES
        )

    if not creds or not creds.valid:

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDS_FILE,
                SCOPES
            )

            auth_url, _ = flow.authorization_url(
                access_type="offline",
                prompt="consent"
            )

            print("\nOpen this URL in any browser:")
            print(auth_url)

            code = input("\nPaste authorization code here: ")

            flow.fetch_token(code=code)

            creds = flow.credentials

        TOKEN_FILE.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        TOKEN_FILE.write_text(
            creds.to_json()
        )

    vault = CredentialVault()

    vault.save(
        "gmail",
        json.loads(TOKEN_FILE.read_text())
    )

    print("GMAIL OAUTH CONNECTED")


if __name__ == "__main__":
    main()
