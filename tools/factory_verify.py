import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ai.factory.runtime import FactoryRuntime


def check(name, condition):
    status = "PASS" if condition else "FAIL"
    print(f"{name}: {status}")
    return condition


def main():
    print("FACTORY VERIFICATION")
    print("=" * 40)

    passed = True

    try:
        factory = FactoryRuntime()
        passed &= check("Runtime initialization", True)
    except Exception as exc:
        print("Runtime initialization: FAIL")
        print(exc)
        return False

    checks = {
        "Operations Intelligence":
            hasattr(factory, "operations_intelligence"),

        "Improvement Executor":
            hasattr(factory, "improvement_executor"),

        "Decision Adapter":
            hasattr(factory, "decision_option_adapter"),

        "Improvement Approval":
            hasattr(factory, "improvement_approval"),

        "Improvement Audit":
            hasattr(factory, "improvement_audit"),
    }

    for name, value in checks.items():
        passed &= check(name, value)

    try:
        report = factory.get_operations_report()

        passed &= check(
            "Operations Report",
            isinstance(report, dict)
            and "system_loop" in report
        )

    except Exception as exc:
        print("Operations Report: FAIL")
        print(exc)
        passed = False

    print("=" * 40)

    print(
        "FACTORY STATUS:",
        "READY" if passed else "ISSUES FOUND"
    )

    return passed


if __name__ == "__main__":
    main()
