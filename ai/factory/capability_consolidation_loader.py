import json
from pathlib import Path


class FactoryCapabilityConsolidationLoader:

    def __init__(self, path="state/capability_consolidation_report.json"):
        self.path = Path(path)

    def load(self):
        if not self.path.exists():
            return {
                "status": "NO_CONSOLIDATION_REPORT",
                "archived_candidates": [],
                "resolved_candidates": [],
                "verified_core": [],
            }

        return json.loads(
            self.path.read_text()
        )
