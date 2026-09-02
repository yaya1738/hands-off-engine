"""Verification-only compatibility gate for the historical Factory milestone.

The legacy implementation could stage and commit repository changes directly.
Repository mutation is now owned by the Factory authority boundary; this module
only verifies the milestone inputs and reports that mutation was intentionally
disabled.
"""

from pathlib import Path
import json
import sys


MILESTONE = "factory-runtime-reporting-restored-20260717"

EXPECTED_FILES = [
    "ai/factory/runtime.py",
    "factory_constructor_repair_assistant.py",
    "factory_constructor_contract_audit.py",
    "factory_constructor_contract_analyzer.py",
    "factory_constructor_dependency_usage_audit.py",
    "factory_runtime_constructor_audit.py",
    "factory_pipeline_usage_audit.py",
    "factory_runtime_report_adapter.py",
    "factory_runtime_checkpoint_capture.py",
    "factory_checkpoint_validator.py",
    "factory_runtime_checkpoint.json",
]

EXPECTED_MARKERS = {
    "ai/factory/runtime.py": [
        "FactoryDevelopmentPipeline()",
    ],
    "factory_runtime_checkpoint.json": [
        "factory_runtime_reporting_restored",
        "FactoryRuntime",
        "preflight_runtime_integration",
    ],
}


def check_files():
    return [f for f in EXPECTED_FILES if not Path(f).exists()]


def check_markers():
    failures = []
    for file, markers in EXPECTED_MARKERS.items():
        text = Path(file).read_text()
        for marker in markers:
            if marker not in text:
                failures.append({"file": file, "missing": marker})
    return failures


def main():
    report = {"milestone": MILESTONE, "checks": {}}

    missing = check_files()
    report["checks"]["files"] = {"passed": not missing, "missing": missing}
    if missing:
        print(json.dumps(report, indent=2))
        sys.exit(1)

    marker_failures = check_markers()
    report["checks"]["markers"] = {
        "passed": not marker_failures,
        "failures": marker_failures,
    }
    if marker_failures:
        print(json.dumps(report, indent=2))
        sys.exit(1)

    report["checks"]["repository_mutation"] = {
        "passed": False,
        "disabled": True,
        "authority": "FactoryAuthorityGateway",
    }
    report["next_phase"] = "preflight_runtime_integration"
    report["action"] = "submit repository mutation through FactoryAuthorityGateway"

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
