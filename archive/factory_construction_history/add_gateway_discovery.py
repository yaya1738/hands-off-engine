from pathlib import Path

path = Path("ai/factory/authority_gateway.py")

text = path.read_text()

needle = """    def submit_goal(self, objective):

        goal_state = self.runtime.submit_goal(
            objective
        )
"""

replacement = """    def submit_goal(self, objective):

        discovery = self.runtime.autonomy.discovery_gate(
            objective,
            "authority_gateway_submission",
        )

        goal_state = self.runtime.submit_goal(
            objective
        )
"""

if needle not in text:
    raise SystemExit("Insertion point not found")

text = text.replace(
    needle,
    replacement,
)

old_return = """        return {
            "goal": goal_state,
            "task": task,
            "construction": construction_state,
            "state": "ready_for_review"
        }
"""

new_return = """        return {
            "goal": goal_state,
            "discovery": discovery,
            "task": task,
            "construction": construction_state,
            "state": "ready_for_review"
        }
"""

if old_return not in text:
    raise SystemExit("Return block not found")

text = text.replace(
    old_return,
    new_return,
)

path.write_text(text)

print("updated")
