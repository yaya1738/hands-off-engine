from ai.factory.decision_option_adapter import FactoryDecisionOptionAdapter

adapter = FactoryDecisionOptionAdapter()

plan = {
    "tasks": [
        "improve lifecycle routing",
        "validate execution path",
    ],
    "priority": 5,
    "context": "factory",
    "validation": ["approval"],
    "rollback": ["restore"],
}

options = adapter.build_options(plan)

print("DECISION OPTION ADAPTER")
print("=" * 35)

print("COUNT:", len(options))
print("TYPE:", type(options[0]).__name__)
print("HAS ACTION:", "action" in options[0])
print("HAS SCORE:", "score" in options[0])

print("DONE")
