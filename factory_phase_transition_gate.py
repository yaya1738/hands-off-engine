from pathlib import Path
import subprocess
import json
import sys


CURRENT_MILESTONE = "factory-runtime-reporting-restored-20260717"

NEXT_PHASE = "preflight_runtime_integration"

ALLOWED_NEXT_PHASE_PREFIXES = [
    "factory_autonomy_preflight",
    "factory_capability_",
    "factory_execution_",
    "factory_reporting_",
    "factory_validation_",
]


def run(cmd):
    return subprocess.check_output(
        cmd,
        text=True,
    ).strip()


def main():
    result = {
        "current_milestone": CURRENT_MILESTONE,
        "next_phase": NEXT_PHASE,
        "checks": {},
    }

    latest = run(
        ["git", "log", "-1", "--pretty=%s"]
    )

    result["checks"]["milestone_commit"] = {
        "passed": latest == CURRENT_MILESTONE,
        "found": latest,
    }

    untracked = run(
        ["git", "ls-files", "--others", "--exclude-standard"]
    ).splitlines()

    unexpected = []

    for item in untracked:
        if not any(
            item.startswith(prefix)
            for prefix in ALLOWED_NEXT_PHASE_PREFIXES
        ):
            unexpected.append(item)

    result["checks"]["workspace_separation"] = {
        "passed": not unexpected,
        "unexpected_files": unexpected,
    }

    result["ready"] = all(
        check["passed"]
        for check in result["checks"].values()
    )

    if result["ready"]:
        result["action"] = (
            "begin preflight_runtime_integration"
        )
    else:
        result["action"] = (
            "resolve boundary issues before continuing"
        )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )

    if not result["ready"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
