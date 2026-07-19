from pathlib import Path
import re

path = Path("ai/factory/action_router.py")

text = path.read_text(errors="ignore")

checks = {
    "approval_checks": [
        "approve",
        "approval",
        "APPROVED",
        "improvement_approval",
    ],
    "runtime_routing": [
        "runtime",
        "FactoryRuntime",
        "autonomous_execute",
        "process_approved_improvement",
        "execute_approved_improvement",
    ],
    "direct_execution": [
        "executor",
        ".execute(",
        "subprocess",
        "dispatch",
        "action(",
    ],
    "authority_gateway": [
        "AuthorityGateway",
        "authority_gateway",
    ],
}

print("ACTION ROUTER AUTHORITY SUMMARY")
print("=" * 40)

for category, terms in checks.items():
    hits = []
    for term in terms:
        if term in text:
            hits.append(term)

    print(category.upper(), ":", hits if hits else "NONE")

print("\nEXECUTION LINES:")
for line in text.splitlines():
    if any(
        term in line
        for term in [
            "execute",
            "executor",
            "dispatch",
            "approve",
            "runtime",
        ]
    ):
        print(line.strip())

print("DONE")
