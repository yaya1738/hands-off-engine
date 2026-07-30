from typing import Dict, Any


class FactoryAuthorityRegistry:
    """
    Single source of truth for Factory authority ownership.

    Phase 1:
    - registration only
    - validation only
    - no behavior changes
    """

    AUTHORITY_DOMAINS = {
        "execution": [],
        "decision": [],
        "learning": [],
        "improvement": [],
        "governance": [],
    }

    def __init__(self):
        self.components: Dict[str, Dict[str, Any]] = {}
        self.authorities = {
            key: []
            for key in self.AUTHORITY_DOMAINS
        }

    def register(
        self,
        name: str,
        component: Any,
        authority: str | None = None,
    ):
        entry = {
            "name": name,
            "type": type(component).__name__,
            "module": type(component).__module__,
            "authority": authority,
        }

        self.components[name] = entry

        if authority:
            if authority not in self.authorities:
                self.authorities[authority] = []

            self.authorities[authority].append(
                name
            )

        return entry

    def get_component(self, name):
        return self.components.get(name)

    def authority_map(self):
        return self.authorities

    def components_map(self):
        return self.components

    def validate_unique_authority(self):
        duplicates = {}

        for authority, members in self.authorities.items():
            if len(members) > 1:
                duplicates[authority] = members

        return {
            "healthy": len(duplicates) == 0,
            "duplicates": duplicates,
        }
