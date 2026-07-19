from ai.factory.runtime import FactoryRuntime

factory = FactoryRuntime()

result = factory.submit_development_request(
    "lifecycle answer test",
    "trace"
)

goal = factory.goal_management.history()[-1]
task = factory.development_tracker.history()[-1]
approval = factory.improvement_approval.history()[-1]
audit = factory.improvement_audit.history()[-1]

print("FACTORY LIFECYCLE ANSWER")
print("=" * 35)

checks = [
    ("GOAL -> TASK", bool(goal.get("goal") and task.get("task"))),
    ("TASK ID EXISTS", bool(task.get("id"))),
    ("ARTIFACT LINK", "artifact_id" in str(task)),
    ("APPROVAL LINK", bool(approval.get("improvement"))),
    ("AUDIT LINK", bool(audit.get("action"))),
]

for name, value in checks:
    print(name + ":", "YES" if value else "NO")

chain = all(v for _, v in checks)

print()
print(
    "LIFECYCLE TRACE POSSIBLE:",
    "YES" if chain else "NO"
)

print("NEXT ACTION:")
print(
    "BUILD TRACE ADAPTER"
    if chain
    else "ADD MISSING CONNECTION"
)
