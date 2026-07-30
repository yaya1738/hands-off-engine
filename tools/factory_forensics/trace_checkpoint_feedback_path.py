from ai.factory.runtime import FactoryRuntime
import inspect

r = FactoryRuntime()

checks = {}

checks["emit_event_exists"] = hasattr(r, "emit_event")

learning = getattr(r, "learning", None)

checks["learning_exists"] = learning is not None

if learning:
    methods = [
        x for x in dir(learning)
        if not x.startswith("_")
    ]

    checks["learning_methods"] = methods[:10]

audit = getattr(r, "improvement_audit", None)

checks["audit_exists"] = audit is not None

if audit:
    checks["audit_type"] = type(audit).__name__

print({
    "status": "ANALYZED",
    "checks": checks,
    "next_action": "CONNECT_CHECKPOINT_OUTPUT"
})
