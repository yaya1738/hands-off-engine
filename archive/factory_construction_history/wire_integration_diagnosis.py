from pathlib import Path

target = Path("ai/factory/autonomous_integration_supervisor.py")

source = target.read_text()

if "FactoryAutonomousIntegrationDiagnosis" in source:
    print({"status": "ALREADY_WIRED"})
    raise SystemExit

source = source.replace(
    "from typing import Any, Dict",
    "from typing import Any, Dict\nfrom ai.factory.autonomous_integration_diagnosis import FactoryAutonomousIntegrationDiagnosis",
)

source = source.replace(
    "self._history = []",
    "self._history = []\n        self.diagnosis = FactoryAutonomousIntegrationDiagnosis()",
)

old = """        report[\"healthy\"] = len(report[\"missing\"]) == 0

        self._history.append(report)

        return report
"""

new = """        report[\"healthy\"] = len(report[\"missing\"]) == 0

        if not report[\"healthy\"]:
            report[\"diagnosis\"] = self.diagnosis.diagnose(report)

        self._history.append(report)

        return report
"""

if old not in source:
    raise SystemExit("inspection return block not found")

source = source.replace(old, new)

target.write_text(source)

print({
    "status": "DIAGNOSIS_WIRED",
    "target": str(target),
})
