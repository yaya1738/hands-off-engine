from ai.factory.runtime import FactoryRuntime

r = FactoryRuntime()

goal = {
    "type": "capability_gap",
    "target": "AUTONOMOUS_IMPROVEMENT_INVOCATION_MANAGER",
    "reason": "Factory generated improvement objective"
}

result = r.execute(goal)

print({
    "status": "EXECUTED",
    "result": result,
    "learning_count": len(
        getattr(r.learning, "experiences", [])
    ),
    "audit_available": hasattr(
        r,
        "improvement_audit"
    )
})
