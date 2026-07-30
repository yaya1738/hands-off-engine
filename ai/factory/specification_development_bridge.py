from typing import Any, Dict, List


class FactorySpecificationDevelopmentBridge:
    def __init__(self):
        self._history: List[Dict[str, Any]] = []

    def create_development_request(
        self,
        specification: Dict[str, Any],
    ):
        request = {
            "component": specification.get(
                "name",
                "unknown",
            ),
            "purpose": specification.get(
                "purpose",
                "",
            ),
            "responsibilities": specification.get(
                "responsibilities",
                [],
            ),
            "dependencies": specification.get(
                "dependencies",
                [],
            ),
            "integration_points": specification.get(
                "integration_points",
                [],
            ),
            "interfaces": specification.get(
                "interfaces",
                [],
            ),
            "verification_criteria": specification.get(
                "verification_criteria",
                [],
            ),
            "failure_modes": specification.get(
                "failure_modes",
                [],
            ),
            "status": "DEVELOPMENT_REQUEST_CREATED",
        }

        self._history.append(request)

        return {
            "created": True,
            "request": request,
        }

    def validate_request(
        self,
        request: Dict[str, Any],
    ):
        valid = bool(
            request.get("component")
            and request.get("purpose")
            and request.get("responsibilities")
        )

        return {
            "valid": valid,
            "component": request.get("component"),
        }

    def history(self):
        return self._history
