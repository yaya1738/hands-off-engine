from pathlib import Path

ROOT = Path.cwd()
VERIFIER = ROOT / "verify_process_approval_identity_boundary.py"

print("=== FIX PROCESS APPROVAL IDENTITY VERIFIER ===")
print(f"Repository: {ROOT}")

if not VERIFIER.exists():
    raise SystemExit(f"[ABORTED] Missing verifier: {VERIFIER}")

source = VERIFIER.read_text()

old = '''if processor is not None:
    calls_executor = []

    for node in ast.walk(processor):
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "execute"
                and isinstance(node.func.value, ast.Attribute)
                and node.func.value.attr == "improvement_executor"
            ):
                calls_executor.append(node)

    if calls_executor:
        print(
            "processor -> improvement_executor.execute: PASS"
        )
    else:
        print(
            "processor -> improvement_executor.execute: FAIL"
        )
        failed = True
'''

new = '''if processor is not None:
    processor_calls_execution_helper = False

    for node in ast.walk(processor):
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "execute_approved_improvement"
            ):
                processor_calls_execution_helper = True

    if processor_calls_execution_helper:
        print(
            "processor -> execute_approved_improvement: PASS"
        )
    else:
        print(
            "processor -> execute_approved_improvement: FAIL"
        )
        failed = True


print("\\n=== EXECUTOR HELPER BOUNDARY CHECK ===")

execution_helper = None

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        if node.name == "execute_approved_improvement":
            execution_helper = node
            break

if execution_helper is None:
    print(
        "execute_approved_improvement definition: FAIL"
    )
    failed = True
else:
    executor_calls = []

    for node in ast.walk(execution_helper):
        if isinstance(node, ast.Call):
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "execute"
                and isinstance(node.func.value, ast.Attribute)
                and node.func.value.attr == "improvement_executor"
            ):
                executor_calls.append(node)

    if executor_calls:
        print(
            "execute_approved_improvement -> "
            "improvement_executor.execute: PASS"
        )
    else:
        print(
            "execute_approved_improvement -> "
            "improvement_executor.execute: FAIL"
        )
        failed = True
'''

if old not in source:
    if new in source:
        print("Verifier is already corrected.")
    else:
        raise SystemExit(
            "[ABORTED] Expected verifier block was not found exactly."
        )
else:
    VERIFIER.write_text(source.replace(old, new, 1))
    print("Verifier updated.")

print("\n=== COMPLETE ===")
print("Verifier-only correction applied.")
print("Production files were not modified.")
print("No commit was created.")
