from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

old = """        from factory_autonomous_decision_reporter import (
            FactoryAutonomousDecisionReporter
        )

        reporter = FactoryAutonomousDecisionReporter()

        decision = reporter.summarize(
            objective
        )
"""

new = """        from factory_runtime_autonomy_gateway import (
            FactoryRuntimeAutonomyGateway
        )

        gateway = FactoryRuntimeAutonomyGateway()

        evaluation = gateway.evaluate(
            objective
        )

        decision = evaluation.get(
            "activation",
            {}
        ).get(
            "decision",
            {}
        )
"""

if old not in text:
    raise SystemExit("target block not found")

text = text.replace(old, new)

path.write_text(text)

print("autonomous execute gateway patch applied")
