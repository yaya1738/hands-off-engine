"""
Hands-Off Credential State Reconciler

Aligns lifecycle state with provider reality.
"""

from datetime import datetime, timezone

from autonomous.credentials.lifecycle import CredentialLifecycle
from autonomous.integrations.providers.gmail_oauth import GmailOAuth


class CredentialStateReconciler:

    def __init__(self):
        self.lifecycle = CredentialLifecycle()
        self.gmail = GmailOAuth()

    def reconcile(self, identity="gmail"):

        current = self.lifecycle.get_state(identity)

        status = self.gmail.status()

        connected = status.get("connected", False)
        token = status.get("token_present", False)

        result = {
            "identity": identity,
            "current": current,
            "provider": {
                "connected": connected,
                "token_present": token,
            },
            "action": "none",
        }

        if (
            current == "VALIDATING"
            and connected
            and token
        ):
            result["transition"] = self.lifecycle.transition(
                identity,
                "ACTIVE",
                "credential_validation_success",
            )

            result["action"] = "activated"

        elif (
            current == "VALIDATING"
            and not token
        ):
            result["action"] = "awaiting_external_authorization"

        return result


def run():
    return CredentialStateReconciler().reconcile()


if __name__ == "__main__":
    print(run())
