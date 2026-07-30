from pathlib import Path

target = Path("ai/factory/runtime.py")

source = target.read_text()

if "FactoryAutonomousIntegrationSupervisor" in source:
    print({
        "status": "ALREADY_WIRED"
    })
    raise SystemExit

import_anchor = "from ai.factory.improvement_audit import FactoryImprovementAudit"

source = source.replace(
    import_anchor,
    import_anchor + "\nfrom ai.factory.autonomous_integration_supervisor import FactoryAutonomousIntegrationSupervisor",
    1,
)

init_anchor = "        self.improvement_audit = FactoryImprovementAudit()"

source = source.replace(
    init_anchor,
    init_anchor + "\n        self.integration_supervisor = FactoryAutonomousIntegrationSupervisor(self)",
    1,
)

target.write_text(source)

print({
    "status": "WIRED",
    "target": str(target),
})
