from pathlib import Path

path = Path("ai/factory/runtime.py")

source = path.read_text()

old = """            repair_route = None

            if hasattr(self, "route_autonomous_failure_repair"):
                repair_route = self.route_autonomous_failure_repair(
                    failure
                )
"""

new = """            repair_route = None

            if hasattr(self, "route_autonomous_failure_repair"):
                repair_route = self.route_autonomous_failure_repair(
                    failure
                )

            if hasattr(self, "improvement_audit"):
                self.improvement_audit.record({
                    "type": "autonomous_failure_recovery",
                    "failure": failure,
                    "repair_route": repair_route,
                })
"""

if "autonomous_failure_recovery" in source:
    print({"status": "ALREADY_PATCHED"})
    raise SystemExit

if old not in source:
    print({"status": "ANCHOR_NOT_FOUND"})
    raise SystemExit

source = source.replace(old, new, 1)

path.write_text(source)

print({
    "status": "FAILURE_RECOVERY_AUDIT_BRIDGE_INSTALLED",
    "target": str(path),
})
