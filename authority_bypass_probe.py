from pathlib import Path
import re

files = [
    "autonomous_loop.py",
    "self_improvement.py",
    "autonomy_manager.py",
    "external_interface.py",
    "action_router.py",
    "development_executor.py",
    "development_orchestrator.py",
]

patterns = [
    "FactoryImprovementExecutor",
    "execute(",
    "approve",
    "request",
    "FactoryAuthorityGateway",
    "FactoryRuntime",
]

print("AUTHORITY BYPASS AUDIT")
print("=" * 35)

for name in files:
    path = Path("ai/factory") / name

    if not path.exists():
        continue

    print("\nFILE:", name)

    text = path.read_text(errors="ignore")

    for line in text.splitlines():
        for p in patterns:
            if p in line:
                print(line.strip())
                break

print("\nDONE")
