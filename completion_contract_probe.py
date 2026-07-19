from ai.factory.runtime import FactoryRuntime
import inspect

runtime = FactoryRuntime()

checks = [
    ("executor", runtime.improvement_executor.execute),
    ("audit", runtime.improvement_audit.record),
    ("learning", runtime.learning_loop.record_outcome),
    ("feedback", runtime.feedback_engine),
    ("pipeline", runtime.development_pipeline.run_development_cycle),
]

print("COMPLETION CONTRACT PROBE")
print("=" * 35)

for name, obj in checks:
    print("\n", name.upper())

    if callable(obj):
        print(inspect.signature(obj))
        print(inspect.getsource(obj)[:600])
    else:
        print("TYPE:", type(obj).__name__)
        print(
            [
                m for m in dir(obj)
                if not m.startswith("_")
            ]
        )

print("\nDONE")
