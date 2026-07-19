from pathlib import Path
import json
import subprocess
from datetime import datetime, timezone


OUTPUT = Path("factory_autonomy_preflight_report.json")


STAGES = [
    "factory_capability_scanner.py",
    "factory_capability_analyzer.py",
    "factory_capability_decision_engine.py",
    "factory_capability_integration_planner.py",
    "factory_capability_safety_gate.py",
    "factory_capability_execution_adapter.py",
    "factory_execution_integration_discovery.py",
    "factory_execution_binding_planner.py",
    "factory_validation_resolver.py",
]


REPORT_FILES = [
    "factory_capability_report.json",
    "factory_capability_analysis.json",
    "factory_capability_decisions.json",
    "factory_capability_integration_plan.json",
    "factory_capability_execution_request.json",
    "factory_capability_execution_plan.json",
    "factory_execution_integration_discovery.json",
    "factory_execution_binding_plan.json",
    "factory_validation_plan.json",
]


def run_stage(stage):
    result = subprocess.run(
        ["python", stage],
        capture_output=True,
        text=True,
    )

    return {
        "stage": stage,
        "return_code": result.returncode,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-2000:],
    }


def load_outputs():
    outputs = {}

    for file in REPORT_FILES:
        path = Path(file)

        if path.exists():
            try:
                outputs[file] = json.loads(
                    path.read_text()
                )
            except Exception:
                outputs[file] = {
                    "error": "unable to parse"
                }

    return outputs


def main():
    stages = []

    for stage in STAGES:
        if Path(stage).exists():
            stages.append(
                run_stage(stage)
            )

    report = {
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "stages": stages,
        "outputs": load_outputs(),
    }

    OUTPUT.write_text(
        json.dumps(
            report,
            indent=2,
        )
    )

    print(
        "Factory autonomy preflight complete"
    )

    print(
        f"Report: {OUTPUT}"
    )


if __name__ == "__main__":
    main()
