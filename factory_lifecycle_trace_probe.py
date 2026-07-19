from ai.factory.runtime import FactoryRuntime

print("FACTORY LIFECYCLE TRACE PROBE")
print("=" * 45)

factory = FactoryRuntime()

components = {
    "goals": "goal_management",
    "development_tracker": "development_tracker",
    "pipeline": "development_pipeline",
    "approval": "improvement_approval",
    "executor": "improvement_executor",
    "audit": "improvement_audit",
    "learning": "learning_loop",
    "feedback": "feedback_engine",
}

for name, attr in components.items():
    component = getattr(factory, attr, None)

    print("\nCOMPONENT:", name)

    if component is None:
        print("STATUS: MISSING")
        continue

    print("TYPE:", type(component).__name__)

    history = getattr(component, "history", None)

    if callable(history):
        try:
            result = history()
            print("HISTORY COUNT:", len(result))
            if result:
                print("LATEST KEYS:", list(result[-1].keys()))
        except Exception as exc:
            print("HISTORY ERROR:", exc)
    else:
        print("HISTORY: NOT EXPOSED")

print("\nDONE")
