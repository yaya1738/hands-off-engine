from typing import Any, Dict


class FactoryBootstrap:
    def __init__(
        self,
        components: Dict[str, Any],
    ):
        self.components = components
        self.runtime = None

    def create_factory(self):
        self.runtime = self.components[
            "runtime_coordinator"
        ]

        return self.runtime

    def start_factory(self):
        if not self.runtime:
            self.create_factory()

        return self.runtime.initialize()

    def get_runtime(self):
        return self.runtime
