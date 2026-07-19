from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

print("ASSESSMENT → PLANNER BRIDGE")
print("=" * 35)

gaps = factory.improvement_assessment.detect_gaps()

print("GAPS TYPE:", type(gaps).__name__)

if isinstance(gaps, list):
    print("GAP COUNT:", len(gaps))

plan = factory.improvement_planner.plan(
    {"gaps": gaps}
)

print("TASK COUNT:", len(plan.get("tasks", [])))

print("DONE")
