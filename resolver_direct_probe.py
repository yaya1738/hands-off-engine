from ai.factory.improvement_action_resolver import FactoryImprovementActionResolver

resolver = FactoryImprovementActionResolver()

print("RESOLVER CHECK")
print("=" * 20)

result = resolver.resolve({
    "action": "address low success rate"
})

print("RESULT:", result)
print("DONE")
