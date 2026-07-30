from pathlib import Path

path = Path("ai/factory/runtime.py")

source = path.read_text()

old = """            if feedback_goal and hasattr(self, "execute"):
                repair_execution = self.execute(
                    repair_objective
                )
"""

new = """            if hasattr(self, "route_autonomous_failure_repair"):
                repair_execution = self.route_autonomous_failure_repair(
                    failure
                )
"""

if old not in source:
    print({"status": "ANCHOR_NOT_FOUND"})
    raise SystemExit

source = source.replace(old, new, 1)

path.write_text(source)

print({
    "status": "FAILURE_REPAIR_LOOP_FIXED",
    "target": str(path),
})
