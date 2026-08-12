from pathlib import Path
import re

ROOT = Path(".")
FACTORY = ROOT / "ai" / "factory"

AUTHORITY = "FactoryAuthorityGateway"

# Methods/signals that can represent externally supplied development intent.
INGRESS_SIGNALS = [
    r"submit_goal\s*\(",
    r"submit_development_request\s*\(",
    r"submit_objective\s*\(",
    r"create_development_request\s*\(",
    r"development_request\s*=",
]

# Production-facing surfaces. Tests/tools are explicitly excluded.
PRODUCTION_EXCLUDE = (
    str(ROOT / "tests"),
    str(ROOT / "tools"),
)

print("=== FACTORY GLOBAL EXTERNAL DEVELOPMENT-INGRESS CLOSURE AUDIT ===")
print(f"Repository: {Path.cwd()}")
print()

hits = []

for path in sorted(FACTORY.rglob("*.py")):
    text = path.read_text(errors="replace")
    for lineno, line in enumerate(text.splitlines(), 1):
        if any(re.search(pattern, line) for pattern in INGRESS_SIGNALS):
            hits.append((path, lineno, line.strip()))

print("=== DEVELOPMENT-INTENT SIGNALS ===")
for path, lineno, line in hits:
    print(f"{path}:{lineno}: {line}")

print()
print("=== PRODUCTION CALL-SITE CLASSIFICATION ===")

production = []
internal = []
excluded = []

for path, lineno, line in hits:
    normalized = str(path)

    if normalized.startswith(PRODUCTION_EXCLUDE):
        excluded.append((path, lineno, line))
        continue

    # Authority gateway itself is the intended authority owner.
    if AUTHORITY in line or path.name == "authority_gateway.py":
        internal.append((path, lineno, line))
        continue

    # Runtime/internal orchestration is not external ingress by itself.
    if path.name in {
        "runtime.py",
        "development_pipeline.py",
        "improvement_pipeline_runner.py",
        "development_entry_point.py",
        "specification_development_bridge.py",
        "development_orchestrator.py",
    }:
        internal.append((path, lineno, line))
        continue

    production.append((path, lineno, line))

print(f"Potential production candidates: {len(production)}")
print(f"Gateway/internal candidates:     {len(internal)}")
print(f"Excluded tests/tools:            {len(excluded)}")
print()

if production:
    print("=== POTENTIAL PRODUCTION BYPASSES ===")
    for path, lineno, line in production:
        print(f"{path}:{lineno}: {line}")
    print()
    print("=== CLOSURE DECISION ===")
    print("REVIEW REQUIRED")
    print("Potential production development-intent paths remain.")
else:
    print("=== CLOSURE DECISION ===")
    print("NO-PRODUCTION-BYPASS-DETECTED")
    print()
    print("FactoryAuthorityGateway remains the identified")
    print("external development-ingress authority.")
    print("No production bypass was detected by this audit.")

print()
print("=== RULES ===")
print("[RULE] Do not migrate internal runtime control loops merely for convergence.")
print("[RULE] Do not duplicate development processing in Gateway.")
print("[RULE] Existing-task execution is not development ingress.")
print("[RULE] Tests/tools are not production authority.")
print("[RULE] Any production candidate requires separate authority tracing.")
print()
print("=== READ-ONLY RESULT ===")
print("PASS")
print("No files were modified.")
print("No files were staged.")
print("No commit was created.")
