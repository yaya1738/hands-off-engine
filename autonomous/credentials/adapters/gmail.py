"""
Hands-Off Gmail Credential Adapter

Google-specific credential handling lives here.
The core credential system only sees normalized states.
"""

from autonomous.integrations.providers.gmail_oauth import GmailOAuth


class GmailCredentialAdapter:

    def provider(self):
        return "gmail"

    def __init__(self):
        self.connector = GmailOAuth()

    def acquire(self, request):
        """
        Begin acquisition workflow.

        External authorization requirements stay inside adapter.
        """

        return {
            "provider": self.provider(),
            "capability": request.get("capability"),
            "status": "awaiting_authorization",
            "next_action": "complete_gmail_oauth"
        }

    def status(self):
        """
        Return normalized provider state.
        """

        result = self.connector.status()

        return {
            "provider": self.provider(),
            "connected": result.get("connected", False),
            "token_present": result.get("token_present", False)
        }

    def validate(self):
        return self.status()
