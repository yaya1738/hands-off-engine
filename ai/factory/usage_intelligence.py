from datetime import datetime, timezone
import os


class FactoryUsageIntelligence:

    def __init__(self, runtime):
        self.runtime = runtime


    def analyze(self):

        components = (
            self.runtime
            .component_inventory()
            .get("components", [])
        )

        usage = {}

        for component in components:

            usage[component] = {
                "references_found": self.find_references(component),
                "status": "analyzed"
            }

        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "usage":
                usage,

            "status":
                "usage_analysis_complete"
        }


    def find_references(self, component):

        count = 0

        root = "ai"

        try:
            for path, dirs, files in os.walk(root):

                for file in files:

                    if file.endswith(".py"):

                        full = os.path.join(
                            path,
                            file
                        )

                        with open(
                            full,
                            "r",
                            errors="ignore"
                        ) as f:

                            if component in f.read():
                                count += 1

        except Exception:
            pass

        return count
