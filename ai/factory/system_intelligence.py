from datetime import datetime, timezone


class FactorySystemIntelligence:

    def __init__(self, runtime):
        self.runtime = runtime

    def analyze(self):

        inventory = self.runtime.component_inventory()

        components = inventory.get(
            "components",
            []
        )

        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component_count":
                len(components),

            "components":
                components,

            "recommendation":
                self._recommend(
                    len(components)
                )
        }


    def _recommend(self, count):

        if count > 40:
            return "begin_consolidation"

        return "continue_growth"
