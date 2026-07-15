from typing import Any, Dict, List


class FactoryAccessControl:
    def __init__(self):
        self.identities: Dict[str, Dict[str, Any]] = {}
        self.permissions: Dict[str, List[str]] = {}
        self._history: List[Dict[str, Any]] = []

    def register_identity(
        self,
        identity: str,
        data: Dict[str, Any],
    ):
        self.identities[identity] = data

        result = {
            "registered": True,
            "identity": identity,
        }

        self._history.append(
            result
        )

        return result

    def grant_permission(
        self,
        identity: str,
        permission: str,
    ):
        self.permissions.setdefault(
            identity,
            []
        ).append(
            permission
        )

        result = {
            "granted": True,
            "identity": identity,
            "permission": permission,
        }

        self._history.append(
            result
        )

        return result

    def check_permission(
        self,
        identity: str,
        permission: str,
    ):
        result = {
            "allowed": permission in self.permissions.get(
                identity,
                []
            ),
        }

        self._history.append(
            result
        )

        return result

    def revoke_permission(
        self,
        identity: str,
        permission: str,
    ):
        if permission in self.permissions.get(
            identity,
            []
        ):
            self.permissions[identity].remove(
                permission
            )

        result = {
            "revoked": True,
            "identity": identity,
            "permission": permission,
        }

        self._history.append(
            result
        )

        return result

    def history(self):
        return self._history
