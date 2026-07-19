from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("ACTION RESOLUTION CHECK")
print("=" * 35)

selected = {
    "action": "address low success rate",
    "score": 0,
    "context": "assessment",
    "validation": [],
    "rollback": [],
}

handler = factory.improvement_action_resolver.resolve(selected)

print("HANDLER:", handler)

print("DONE")
