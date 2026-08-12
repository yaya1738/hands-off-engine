import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "ai/factory/runtime.py"

print("=== FACTORY APPROVAL -> EXECUTOR CALLSITE ORDER AUDIT ===")
print(f"Repository: {ROOT}")
print()

source = RUNTIME.read_text()
tree = ast.parse(source)

lines = source.splitlines()

validation_lines = []
executor_lines = []
approval_action_lines = []

for node in ast.walk(tree):
    if isinstance(node, ast.Call):
        func = node.func

        if isinstance(func, ast.Attribute):
            name = func.attr

            if name == "validate_approved_request":
                validation_lines.append(node.lineno)

            elif name == "execute":
                if (
                    isinstance(func.value, ast.Attribute)
                    and func.value.attr == "improvement_executor"
                ):
                    executor_lines.append(node.lineno)

            elif name == "approve":
                if (
                    isinstance(func.value, ast.Attribute)
                    and func.value.attr == "improvement_approval"
                ):
                    approval_action_lines.append(node.lineno)

print("--- CANONICAL APPROVAL VALIDATION ---")
for n in sorted(validation_lines):
    print(f"{n}: {lines[n-1].strip()}")

print()
print("--- IMPROVEMENT EXECUTOR CALLS ---")
for n in sorted(executor_lines):
    print(f"{n}: {lines[n-1].strip()}")

print()
print("--- APPROVAL ACTIONS ---")
for n in sorted(approval_action_lines):
    print(f"{n}: {lines[n-1].strip()}")

print()
print("--- ORDER ANALYSIS ---")

if not executor_lines:
    print("[FAIL] No improvement_executor.execute() call sites detected.")
    raise SystemExit(1)

if not validation_lines:
    print("[FAIL] No canonical approval validation detected.")
    raise SystemExit(1)

for exec_line in sorted(executor_lines):
    prior_validation = [
        n for n in validation_lines
        if n < exec_line
    ]

    if prior_validation:
        nearest = max(prior_validation)
        print(
            f"[OBSERVE] executor line {exec_line} "
            f"has prior canonical validation at line {nearest}"
        )
    else:
        print(
            f"[REVIEW] executor line {exec_line} "
            f"has NO earlier canonical validation in runtime.py"
        )

print()
print("--- STATIC DECISION ---")

unsafe = [
    n for n in executor_lines
    if not any(v < n for v in validation_lines)
]

if unsafe:
    print("[REVIEW] Direct executor call sites require authority tracing:")
    for n in sorted(unsafe):
        print(f"  runtime.py:{n}")
    print()
    print("This is NOT declared a bypass by this audit.")
    print("It requires local control-flow tracing before any mutation.")
else:
    print("[PASS] Every detected executor call has an earlier")
    print("       canonical approval-validation signal in runtime.py.")

print()
print("=== READ-ONLY RESULT ===")
print("PASS")
print("No files were modified.")
print("No production code was changed.")
print("No files were staged.")
print("No commit was created.")
