from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

checks = [
    "development_translator",
    "development_advisor",
    "development_pipeline",
    "development_tracker",
    "improvement_executor",
    "improvement_approval",
    "improvement_audit",
    "simulation",
    "change_impact_analyzer",
    "artifact_registry",
]

for name in checks:
    print("\nCOMPONENT:", name)

    if hasattr(factory, name):
        component = getattr(factory, name)
        print("STATUS: PRESENT")
        print("TYPE:", type(component).__name__)

        methods = [
            m for m in dir(component)
            if not m.startswith("_")
        ]

        print("METHODS:", methods[:15])

    else:
        print("STATUS: MISSING")
