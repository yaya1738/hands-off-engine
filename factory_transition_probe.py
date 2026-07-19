from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

result = factory.autonomy.discovery_gate(
    "Transition from manual ChatGPT-Termux development workflow to factory-mediated development ingestion",
    "Analyze existing capabilities, missing layers, reusable components, and required architecture transition"
)

print("COMPONENT COUNT:")
print(
    result["component_inventory"].get("component_count")
)

print("\nSYSTEM ANALYSIS:")
print(result["system_analysis"])

print("\nCAPABILITY GRAPH:")
print(result["capability_graph_analysis"])

print("\nCONSOLIDATION DECISION:")
print(result["consolidation_decision_analysis"])
