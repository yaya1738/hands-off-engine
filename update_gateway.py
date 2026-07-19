from pathlib import Path

path = Path("ai/factory/authority_gateway.py")

text = path.read_text()

old = """        discovery = self.runtime.autonomy.discovery_gate(
            objective,
            "authority_gateway_submission",
        )

        goal_state = self.runtime.submit_goal(
            objective
        )

        task = self.tracker.create_task(
            {
                "goal": objective,
                "type": "capability_build"
            }
        )

        construction_state = self.pipeline.run_development_cycle(
            {
                "goal": objective,
                "type": "capability_build"
            }
        )

        return {
            "goal": goal_state,
            "discovery": discovery,
            "task": task,
            "construction": construction_state,
            "state": "ready_for_review"
        }
"""

new = """        development_request = self.runtime.submit_development_request(
            objective,
            "authority_gateway_submission",
        )

        return {
            "development_request": development_request,
            "state": "ready_for_review"
        }
"""

if old not in text:
    raise SystemExit("target block not found")

path.write_text(text.replace(old, new))

print("updated")
