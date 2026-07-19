import inspect
from ai.factory.runtime import FactoryRuntime


ROLE_HINTS = {
    "assessment": ["assess", "detect", "recommend", "metrics"],
    "planning": ["plan", "prioritize"],
    "approval": ["approve"],
    "decision": ["select", "decision", "option"],
    "execution": ["execute", "run"],
    "audit": ["audit", "record", "history"],
    "routing": ["route", "resolve", "register"],
}


def classify(name, obj):
    text = (
        name + " " +
        type(obj).__name__
    ).lower()

    for role, hints in ROLE_HINTS.items():
        if any(h in text for h in hints):
            return role

    return "other"


def public_methods(obj):
    methods = []

    for name in dir(obj):
        if name.startswith("_"):
            continue

        try:
            value = getattr(obj, name)

            if callable(value):
                methods.append(
                    name + str(inspect.signature(value))
                )
        except Exception:
            pass

    return methods


print("FACTORY INTELLIGENCE INSPECTOR")
print("=" * 45)

factory = FactoryRuntime()

groups = {}

for name, obj in vars(factory).items():
    role = classify(name, obj)

    groups.setdefault(role, []).append(
        {
            "name": name,
            "type": type(obj).__name__,
            "methods": public_methods(obj)
        }
    )


for role, items in groups.items():
    print("\n[" + role.upper() + "]")

    for item in items:
        print(
            "✓",
            item["name"],
            "->",
            item["type"]
        )

        important = [
            m for m in item["methods"]
            if any(
                x in m.lower()
                for x in [
                    "execute",
                    "plan",
                    "approve",
                    "select",
                    "resolve",
                    "record",
                    "history",
                    "detect"
                ]
            )
        ]

        for method in important[:5]:
            print("   ", method)


print("\nGAP CHECK")
print("=" * 45)

has_resolver = hasattr(
    factory,
    "improvement_action_resolver"
)

has_executor = hasattr(
    factory,
    "improvement_executor"
)

print(
    "Resolver:",
    "OK" if has_resolver else "MISSING"
)

print(
    "Executor:",
    "OK" if has_executor else "MISSING"
)

if has_resolver and has_executor:
    print(
        "Bridge:",
        "PRESENT (resolver -> executor boundary)"
    )

print("\nDONE")
