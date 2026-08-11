from pathlib import Path
import ast
import subprocess
import sys


ROOT = Path.cwd()
RUNTIME = ROOT / "ai/factory/runtime.py"
APPROVAL = ROOT / "ai/factory/improvement_approval.py"

print("=== PROCESS APPROVAL IDENTITY BOUNDARY VERIFICATION ===")
print(f"Repository: {ROOT}")


if not RUNTIME.exists():
    raise SystemExit(f"[ABORTED] Missing: {RUNTIME}")

if not APPROVAL.exists():
    raise SystemExit(f"[ABORTED] Missing: {APPROVAL}")


runtime_source = RUNTIME.read_text()
approval_source = APPROVAL.read_text()


print("\n=== STATIC AUTHORITY CHECKS ===")

required_runtime_patterns = [
    (
        "process pipeline accepts approval request",
        "def process_approval_pipeline(" in runtime_source,
    ),
    (
        "pipeline passes approval request into processor",
        """self.process_approved_improvement(
            approval_request,
            action,
        )""" in runtime_source,
    ),
    (
        "processor validates through approval authority",
        "self.improvement_approval.validate_approved_request(" in runtime_source,
    ),
    (
        "processor extracts improvement only after validation",
        """improvement = validation.get(
            "improvement"
        )""" in runtime_source,
    ),
]

required_approval_patterns = [
    (
        "canonical approval IDs exist",
        '"approval_id"' in approval_source,
    ),
    (
        "registered request validation exists",
        "def validate_approved_request(" in approval_source,
    ),
    (
        "unregistered requests are blocked",
        '"unregistered_approval_request"' in approval_source,
    ),
    (
        "non-approved requests are blocked",
        '"approval_request_not_approved"' in approval_source,
    ),
]


failed = False

for name, passed in (
    required_runtime_patterns
    + required_approval_patterns
):
    print(f"{name}: {'PASS' if passed else 'FAIL'}")
    if not passed:
        failed = True


print("\n=== AST CALLSITE CHECK ===")

tree = ast.parse(runtime_source)

processor = None
pipeline = None

for node in ast.walk(tree):
    if isinstance(node, ast.FunctionDef):
        if node.name == "process_approved_improvement":
            processor = node
        elif node.name == "process_approval_pipeline":
            pipeline = node

if processor is None:
    print("process_approved_improvement definition: FAIL")
    failed = True
else:
    print("process_approved_improvement definition: PASS")

if pipeline is None:
    print("process_approval_pipeline definition: FAIL")
    failed = True
else:
    print("process_approval_pipeline definition: PASS")


print("\n=== EXECUTION BOUNDARY CHECK ===")

if processor is not None:
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


print("\n=== EXECUTOR HELPER BOUNDARY CHECK ===")

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


print("\n=== PIPELINE IDENTITY CHECK ===")

pipeline_text = ast.get_source_segment(
    runtime_source,
    pipeline,
) if pipeline is not None else ""

if pipeline_text:
    if (
        "approval_request.get(" not in pipeline_text
        or """self.process_approved_improvement(
            approval_request,
            action,
        )""" in pipeline_text
    ):
        print(
            "approval_request preserved into processor: PASS"
        )
    else:
        print(
            "approval_request preserved into processor: FAIL"
        )
        failed = True
else:
    print("Unable to extract pipeline source: FAIL")
    failed = True


print("\n=== PYTHON COMPILE CHECK ===")

compile_result = subprocess.run(
    [
        sys.executable,
        "-m",
        "py_compile",
        str(APPROVAL),
        str(RUNTIME),
    ],
    cwd=ROOT,
)

if compile_result.returncode == 0:
    print("PASS")
else:
    print("FAIL")
    failed = True


print("\n=== FOCUSED REGRESSION SUITE ===")

pytest_result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "tests/test_process_approval_identity_boundary.py",
        "tests/test_canonical_approval_boundary.py",
        "tests/test_factory_autonomous_failure_closure.py",
        "tests/test_failure_route_registry_closure.py",
    ],
    cwd=ROOT,
)

if pytest_result.returncode == 0:
    print("PASS")
else:
    print("FAIL")
    failed = True


print("\n=== VERIFICATION RESULT ===")

if failed:
    print("FAIL")
    print("Do not commit.")
    raise SystemExit(1)

print("PASS")
print("Canonical approval request identity is preserved through")
print("the approval pipeline into execution.")
print("No files were modified.")
print("No commit was created.")
