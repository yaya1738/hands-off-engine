from pathlib import Path

path = Path("ai/factory/runtime.py")

source = path.read_text()

old = """            diagnostics = None
            feedback_goal = None
"""

new = """            diagnostics = None
            feedback_goal = None
            repair_route = None

            if hasattr(self, "route_autonomous_failure_repair"):
                repair_route = self.route_autonomous_failure_repair(
                    failure
                )
"""

if "repair_route = self.route_autonomous_failure_repair" in source:
    print({"status": "ALREADY_WIRED"})
    raise SystemExit

if old not in source:
    print({"status": "ANCHOR_NOT_FOUND"})
    raise SystemExit

source = source.replace(old, new, 1)

old_return = """                "diagnostics": diagnostics,
                "feedback_goal": feedback_goal,
"""

new_return = """                "diagnostics": diagnostics,
                "feedback_goal": feedback_goal,
                "repair_route": repair_route,
"""

if old_return not in source:
    print({"status": "RETURN_ANCHOR_NOT_FOUND"})
    raise SystemExit

source = source.replace(old_return, new_return, 1)

path.write_text(source)

print({
    "status": "FAILURE_REPAIR_ROUTER_WIRED",
    "target": str(path),
})
