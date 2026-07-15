"""
Hands-Off Credential Aware Integration Supervisor v2
"""

import json

from autonomous.credentials.reconciler import CredentialStateReconciler
from datetime import datetime, timezone


class IntegrationSupervisorV2:

    def __init__(self):
        self.errors = []
        self.reconciler = CredentialStateReconciler()

        try:
            from autonomous.credentials.supervisor import CredentialSupervisor
            self.credentials = CredentialSupervisor()
        except Exception as e:
            self.credentials = None
            self.errors.append(
                f"credential supervisor import: {e}"
            )

        try:
            from autonomous.integrations.providers.gmail_oauth import GmailOAuth
            self.gmail = GmailOAuth()
        except Exception as e:
            self.gmail = None
            self.errors.append(
                f"gmail oauth import: {e}"
            )


    def credential_check(self):

        if not self.credentials:
            return {
                "error": "credential supervisor unavailable"
            }

        try:
            return self.credentials.check_all()
        except Exception as e:
            return {
                "error": str(e)
            }


    def integration_check(self):

        if not self.gmail:
            return {
                "provider": "gmail",
                "error": "gmail adapter unavailable"
            }

        try:
            status = self.gmail.status()

            return {
                "provider": "gmail",
                "connected": status.get(
                    "connected",
                    False
                ),
                "token_present": status.get(
                    "token_present",
                    False
                )
            }

        except Exception as e:
            return {
                "provider": "gmail",
                "error": str(e)
            }


    def run_once(self):

        credentials = self.credential_check()
        gmail = self.integration_check()

        healthy = (
            gmail.get("connected") is True
            and gmail.get("token_present") is True
        )

        return {
            "timestamp": datetime.now(
                timezone.utc
            ).isoformat(),

            "healthy": healthy,

            "errors": self.errors,

            "credentials": credentials,

            "reconciliation": self.reconciler.reconcile(),

            "integration": gmail
        }


def run():
    return IntegrationSupervisorV2().run_once()


if __name__ == "__main__":
    print(
        json.dumps(
            run(),
            indent=2
        )
    )
