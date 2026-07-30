from pathlib import Path

path = Path("ai/factory/runtime.py")

source = path.read_text()

old = """            if hasattr(self, "improvement_audit"):
                self.improvement_audit.record({
                    "type": "autonomous_failure_recovery",
                    "failure": failure,
                    "repair_route": repair_route,
                })
"""

new = """            if hasattr(self, "improvement_audit"):
                recovery_record = self.improvement_audit.record({
                    "type": "autonomous_failure_recovery",
                    "failure": failure,
                    "repair_route": repair_route,
                })

                if hasattr(self, "learning_loop"):
                    self.learning_loop.record_outcome(
                        recovery_record
                    )
"""

if "recovery_record = self.improvement_audit.record" in source:
    print({"status": "ALREADY_PATCHED"})
    raise SystemExit

if old not in source:
    print({"status": "ANCHOR_NOT_FOUND"})
    raise SystemExit

source = source.replace(old, new, 1)

path.write_text(source)

print({
    "status": "FAILURE_LEARNING_BRIDGE_FIXED",
    "target": str(path),
})
