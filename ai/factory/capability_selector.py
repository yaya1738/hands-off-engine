from typing import Any, Dict


class FactoryCapabilitySelector:

    def __init__(self, runtime):
        self.runtime = runtime

    def select(
        self,
        query: str,
    ) -> Dict[str, Any]:

        capabilities = (
            self.runtime
            .improvement_capability_registry
            .list_capabilities()
        )

        matches = [
            name
            for name in capabilities
            if query.lower() in name.lower()
        ]

        if not matches:
            return {
                "selected": False,
                "capability": None,
            }

        performance = getattr(
            self.runtime,
            "capability_performance",
            None,
        )

        if performance is not None and len(matches) > 1:
            matches = sorted(
                matches,
                key=lambda name: (
                    performance.success_rate(name)
                ),
                reverse=True,
            )

        return {
            "selected": True,
            "capability": matches[0],
        }
