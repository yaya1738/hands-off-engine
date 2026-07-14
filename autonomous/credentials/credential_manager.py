import json
from pathlib import Path

from autonomous.credentials.credential_state import (
    CredentialState,
    CredentialStatus,
)


class CredentialManager:

    def __init__(self):
        self.path = Path("data/credentials/state.json")
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.credentials = {}
        self.load()

    def load(self):

        if not self.path.exists():
            return

        data = json.loads(
            self.path.read_text()
        )

        for key, item in data.items():
            self.credentials[key] = CredentialState(
                identity=item["identity"],
                provider=item["provider"],
                capabilities=item["capabilities"],
                status=CredentialStatus(item["status"])
            )

    def save(self):

        self.path.write_text(
            json.dumps(
                {
                    key: value.to_dict()
                    for key, value in self.credentials.items()
                },
                indent=2
            )
        )

    def request(self, request):

        state = CredentialState(
            identity=request.identity,
            provider=request.provider,
            capabilities=[request.capability],
            status=CredentialStatus.AWAITING_AUTHORIZATION,
        )

        self.credentials[request.identity] = state

        self.save()

        return state.to_dict()

    def status(self):

        return {
            key: value.to_dict()
            for key, value in self.credentials.items()
        }
