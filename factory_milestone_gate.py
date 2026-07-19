from pathlib import Path
import subprocess
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


def run(cmd):
    return subprocess.check_output(
        cmd,
        text=True,
    ).strip()


def check_files():
    missing = [
        f for f in EXPECTED_FILES
        if not Path(f).exists()
    ]
    return missing


def check_markers():
    failures = []

    for file, markers in EXPECTED_MARKERS.items():
        text = Path(file).read_text()

        for marker in markers:
            if marker not in text:
                failures.append(
                    {
                        "file": file,
                        "missing": marker,
                    }
                )

    return failures


def git_stage():
    subprocess.run(
        ["git", "add"] + EXPECTED_FILES,
        check=True,
    )


def git_commit():
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            MILESTONE,
        ],
        check=True,
    )


def main():
    report = {
        "milestone": MILESTONE,
        "checks": {},
    }

    missing = check_files()

    report["checks"]["files"] = {
        "passed": not missing,
        "missing": missing,
    }

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

    git_stage()

    report["checks"]["staged"] = {
        "passed": True
    }

    git_commit()

    status = run(
        ["git", "status", "--short"]
    )

    clean = status == ""

    report["checks"]["boundary"] = {
        "passed": clean,
        "status": status,
    }

    if clean:
        report["next_phase"] = (
            "preflight_runtime_integration"
        )
        report["action"] = (
            "begin next phase"
        )

    print(
        json.dumps(
            report,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
