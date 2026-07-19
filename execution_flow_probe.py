from ai.factory.runtime import FactoryRuntime
import inspect

runtime = FactoryRuntime()

targets = [
    "execute_approved_improvement",
    "process_approved_improvement",
    "autonomous_execute",
    "run_improvement_cycle",
]

print("RUNTIME EXECUTION FLOW PROBE")
print("=" * 35)

for name in targets:
    print()
    print("METHOD:", name)

    method = getattr(runtime, name)

    source = inspect.getsource(method)

    lines = [
        line.strip()
        for line in source.splitlines()
        if any(
            word in line.lower()
            for word in [
                "approval",
                "executor",
                "execute",
                "validate",
                "audit",
                "learning",
                "feedback",
                "artifact",
                "queue",
            ]
        )
    ]

    for line in lines:
        print(" ", line)

print()
print("DONE")
