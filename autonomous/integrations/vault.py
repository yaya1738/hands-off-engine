"""
Hands-Off Credential Vault
Stores integration tokens locally.
"""

import json
from pathlib import Path


class CredentialVault:

    def __init__(self):
        self.path = Path("data/secrets/integrations.json")
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, provider, data):
        current = self.load()
        current[provider] = data
        self.path.write_text(
            json.dumps(current, indent=2)
        )

    def load(self):
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text())

    def get(self, provider):
        return self.load().get(provider)


if __name__ == "__main__":
    vault = CredentialVault()
    print(vault.load())
