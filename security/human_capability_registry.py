"""Human capability boundary for non-owner people.

The public repository stores capability policy, not personal contact data.
Identity/contact records are supplied by the private runtime registry.

Default policy:
- David Kaplan: communicate only
- Carol Kaplan: communicate only

No privileged command, trading, approval, credential, or system-admin
capability is granted by this module.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

DEFAULT_CAPABILITIES = {
    "david_kaplan": frozenset({"communicate"}),
    "carol_kaplan": frozenset({"communicate"}),
}

PRIVATE_REGISTRY_CANDIDATES = (
    Path("/root/hands-off-engine/security/human_identity_registry.json"),
    Path(__file__).with_name("human_identity_registry.private.json"),
)


class HumanCapabilityRegistry:
    """Resolve least-privilege capabilities for known human identities."""

    def __init__(self, records: Mapping[str, Any] | None = None):
        self._records = dict(records) if records is not None else self._load_private_records()

    @staticmethod
    def _load_private_records() -> dict[str, Any]:
        for path in PRIVATE_REGISTRY_CANDIDATES:
            if path.exists():
                try:
                    data = json.loads(path.read_text())
                except (OSError, ValueError):
                    return {}
                return data if isinstance(data, dict) else {}
        return {}

    def capabilities_for(self, identity: str) -> frozenset[str]:
        key = self._normalize(identity)
        configured = self._records.get(key)
        if isinstance(configured, dict):
            capabilities = configured.get("capabilities", ())
            if isinstance(capabilities, list):
                return frozenset(str(item) for item in capabilities)
        return DEFAULT_CAPABILITIES.get(key, frozenset())

    def allowed(self, identity: str, capability: str) -> bool:
        return capability in self.capabilities_for(identity)

    @staticmethod
    def _normalize(identity: str) -> str:
        return "_".join(identity.strip().lower().split())


def can_communicate(identity: str) -> bool:
    """Return whether an identity may use the human communication surface."""
    return HumanCapabilityRegistry().allowed(identity, "communicate")
