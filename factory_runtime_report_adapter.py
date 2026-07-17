from pathlib import Path
import json
from ai.factory.runtime import FactoryRuntime


OUTPUT = Path("factory_runtime_unified_report.json")


def collect_report():
    runtime = FactoryRuntime()

    return {
        "factory_report": runtime.factory_report(),
        "trend_report": runtime.trend_report(),
        "integrity_report": runtime.integrity_report(),
        "maintenance_status": runtime.maintenance_status(),
        "operator_status": runtime.operator_status(),
        "history": runtime.history(),
    }


def main():
    report = collect_report()

    OUTPUT.write_text(
        json.dumps(
            report,
            indent=2,
            default=str,
        )
    )

    print(
        "Factory runtime unified report complete"
    )

    print(
        json.dumps(
            report,
            indent=2,
            default=str,
        )[:5000]
    )


if __name__ == "__main__":
    main()
