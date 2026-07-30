from pathlib import Path

path = Path("ai/factory/runtime.py")

source = path.read_text()

anchor = """            if not integration_report.get("healthy", False):
                return {
                    "status": "INTEGRATION_UNHEALTHY",
                    "integration_report": integration_report,
                }
"""

replacement = """            if not integration_report.get("healthy", False):
                return {
                    "status": "INTEGRATION_UNHEALTHY",
                    "integration_report": integration_report,
                }

            self.last_integration_report = integration_report
"""

if "self.last_integration_report = integration_report" in source:
    print({"status": "ALREADY_PATCHED"})
else:
    if anchor not in source:
        print({"status": "ANCHOR_NOT_FOUND"})
        raise SystemExit

    source = source.replace(anchor, replacement)
    path.write_text(source)

    print({
        "status": "RUNTIME_SUPERVISOR_CYCLE_BRIDGE_INSTALLED",
        "target": str(path),
    })
