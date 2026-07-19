from pathlib import Path
import ast

TARGETS = [
    "goal",
    "task",
    "artifact",
    "change",
    "verification",
    "audit",
    "id",
    "status",
]

ROOT = Path("ai/factory")

print("FACTORY LIFECYCLE IDENTITY PROBE")
print("=" * 40)

for path in ROOT.glob("*.py"):
    if "__pycache__" in str(path):
        continue

    try:
        tree = ast.parse(path.read_text(errors="ignore"))
    except Exception:
        continue

    findings = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Str):
            value = node.s
            if any(
                target in value.lower()
                for target in TARGETS
            ):
                findings.append(value)

        if isinstance(node, ast.Name):
            if any(
                target in node.id.lower()
                for target in TARGETS
            ):
                findings.append(node.id)

    if findings:
        unique = sorted(set(findings))
        print("\nCOMPONENT:", path.name)
        print("IDENTITY FIELDS:", unique[:20])

print("\nDONE")
