from pathlib import Path

target = Path("ai/factory/runtime.py")

source = target.read_text()

marker = "# development_pipeline_improvement_bridge"

if marker in source:
    print({
        "status": "ALREADY_INSTALLED"
    })
    raise SystemExit

old = '''            if hasattr(self, "improvement_executor"):
                if action is None:
                    executed.append({
                        "status": "BLOCKED",
                        "reason": "action_resolution_failed"
                    })
                    continue

                result = self.improvement_executor.execute(
                    approved,
                    action
                )
                executed.append(result)
'''

new = '''            if hasattr(self, "improvement_executor"):
                if action is None:
                    executed.append({
                        "status": "BLOCKED",
                        "reason": "action_resolution_failed"
                    })
                    continue

                # development_pipeline_improvement_bridge
                #
                # Route approved autonomous improvements through the
                # existing Factory development pipeline before execution.

                development_result = None

                if hasattr(self, "submit_development_request"):
                    development_result = self.submit_development_request(
                        approved.get(
                            "name",
                            "autonomous improvement"
                        ),
                        "generated from autonomous improvement queue",
                    )

                result = self.improvement_executor.execute(
                    approved,
                    action
                )

                if isinstance(result, dict):
                    result["development"] = development_result

                executed.append(result)
'''

if old not in source:
    raise SystemExit("Execution block not found")

source = source.replace(old, new, 1)

target.write_text(source)

print({
    "status": "DEVELOPMENT_PIPELINE_IMPROVEMENT_BRIDGE_INSTALLED",
    "target": str(target),
})
