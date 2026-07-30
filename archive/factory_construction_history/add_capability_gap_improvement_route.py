from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

old = '''decision["routed_action"] = self.action_router.route(
                adaptive_decision
            )

            if decision["routed_action"].get("action") == "improvement_pipeline":
                improvement_cycle = self.improvement_orchestrator.run_cycle(
                    self.get_assessment_metrics()
                )

                improvement_execution = self.execute_autonomous_improvements(
                    improvement_cycle
                )

                decision["improvement_cycle"] = improvement_cycle
                decision["improvement_execution"] = improvement_execution

            steps.append("decision")
'''

new = '''decision["routed_action"] = self.action_router.route(
                adaptive_decision
            )

            objective = goal.get(
                "objective",
                {}
            )

            if (
                isinstance(objective, dict)
                and objective.get("type") == "capability_gap"
            ):
                improvement_cycle = self.improvement_orchestrator.run_cycle(
                    self.get_assessment_metrics()
                )

                improvement_execution = self.execute_autonomous_improvements(
                    improvement_cycle
                )

                decision["improvement_cycle"] = improvement_cycle
                decision["improvement_execution"] = improvement_execution

            elif decision["routed_action"].get("action") == "improvement_pipeline":
                improvement_cycle = self.improvement_orchestrator.run_cycle(
                    self.get_assessment_metrics()
                )

                improvement_execution = self.execute_autonomous_improvements(
                    improvement_cycle
                )

                decision["improvement_cycle"] = improvement_cycle
                decision["improvement_execution"] = improvement_execution

            steps.append("decision")
'''

if old not in text:
    print({
        "status": "FAILED",
        "reason": "routing_block_not_found"
    })
else:
    path.write_text(text.replace(old, new))
    print({
        "status": "PATCHED",
        "target": "capability_gap_improvement_route",
        "next_action": "VERIFY_COMPILE"
    })
