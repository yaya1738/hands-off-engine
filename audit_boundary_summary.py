import json
from pathlib import Path

checks = []

targets = {
    "FactoryDevelopmentOrchestrator": (
        "ai/factory/development_orchestrator.py",
        "self.executor.execute",
        "direct_executor_access",
        "HIGH",
    ),
    "FactoryJobRunner": (
        "ai/factory/job_runner.py",
        "self.executor.execute",
        "direct_executor_access",
        "HIGH",
    ),
    "FactoryAutonomousLoop": (
        "ai/factory/autonomous_loop.py",
        "router.execute",
        "direct_router_execution",
        "HIGH",
    ),
    "FactoryIntelligenceCoordinator": (
        "ai/factory/intelligence_coordinator.py",
        "self.improvement.execute",
        "direct_improvement_execution",
        "MEDIUM",
    ),
}

for component, (file, pattern, issue, severity) in targets.items():
    path = Path(file)

    if not path.exists():
        continue

    text = path.read_text()

    if pattern in text:
        checks.append(
            {
                "component": component,
                "issue": issue,
                "severity": severity,
            }
        )

report = {
    "authority_model": "runtime_centralized",
    "violations": checks,
    "status": "HEALTHY" if not checks else "BOUNDARY_VIOLATIONS_FOUND",
}

with open(
    "factory_authority_boundary_summary.json",
    "w",
) as f:
    json.dump(report, f, indent=2)

print(json.dumps(report, indent=2))
