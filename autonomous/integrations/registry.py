"""
Hands-Off Integration Registry
Central discovery layer for external services.
"""

import json


class IntegrationRegistry:

    def __init__(self):
        self.providers = {}

        self._load_providers()

    def _load_providers(self):
        try:
            from autonomous.integrations.providers.gmail_oauth import GmailOAuth

            self.providers["gmail"] = GmailOAuth()

        except Exception as e:
            self.providers["gmail"] = {
                "error": str(e)
            }

    def status(self):
        result = {}

        for name, provider in self.providers.items():
            if isinstance(provider, dict):
                result[name] = provider
                continue

            try:
                result[name] = provider.status()
            except Exception as e:
                result[name] = {
                    "error": str(e)
                }

        return result


if __name__ == "__main__":
    print(
        json.dumps(
            IntegrationRegistry().status(),
            indent=2
        )
    )
