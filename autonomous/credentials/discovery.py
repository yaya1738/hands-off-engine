"""
Credential discovery engine.

Finds available credential sources without exposing secrets.
"""

from pathlib import Path
import os


class CredentialDiscovery:

    def __init__(self):
        self.results = {}

    def scan_env(self):
        found = []

        for key in os.environ:
            if any(word in key.lower() for word in [
                "token",
                "secret",
                "key",
                "oauth",
                "credential"
            ]):
                found.append(key)

        return found

    def scan_files(self, root="."):
        matches = []

        patterns = [
            ".env*",
            "*token*.json",
            "*credential*.json",
            "*secret*.json"
        ]

        root = Path(root)

        for pattern in patterns:
            for item in root.rglob(pattern):
                matches.append(str(item))

        return matches

    def run(self):
        self.results = {
            "environment_keys": self.scan_env(),
            "credential_files": self.scan_files()
        }

        return self.results


if __name__ == "__main__":
    import json
    print(
        json.dumps(
            CredentialDiscovery().run(),
            indent=2
        )
    )
