from pathlib import Path
import re

ROOT = Path(".")
FACTORY = ROOT / "ai" / "factory"

print("=== FACTORY DEVELOPMENT-INTENT AUTHORITY CLOSURE AUDIT ===")
print(f"Repository: {ROOT.resolve()}")
print()

# Signals that indicate something is actually creating/submitting
# development intent, rather than merely executing an existing task.
INTENT_SIGNALS = [
    r"submit_development_request\s*\(",
    r"create_development_request\s*\(",
    r"development_request\s*=",
    r"development_goal\s*=",
    r"development_pipeline",
    r"FactoryDevelopmentPipeline",
    r"FactorySpecificationDevelopmentBridge",
    r"create_improvement_proposal\s*\(",
    r"create_capability.*development",
]

EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    "archive",
}

def is_excluded(path):
    return any(part in EXCLUDED_DIRS for part in path.parts)

def context(lines, index, radius=5):
    start = max(0, index - radius)
    end = min(len(lines), index + radius + 1)
    return lines[start:end]

def classify(path, body):
    if path.name == "authority_gateway.py":
        return "AUTHORIZED GATEWAY"

    if path.name == "runtime.py":
        return "RUNTIME INTERNAL / COMPATIBILITY"

    if "FactoryDevelopmentPipeline" in body:
        return "PIPELINE / DOWNSTREAM"

    if "FactorySpecificationDevelopmentBridge" in body:
        return "DEVELOPMENT CONSTRUCTION / DOWNSTREAM"

    if "improvement" in body.lower():
        return "IMPROVEMENT CONTROL LOOP"

    return "UNCLASSIFIED DEVELOPMENT-INTENT CANDIDATE"

print("=== DEVELOPMENT-INTENT SIGNALS ===")

matches = []

for path in sorted(FACTORY.rglob("*.py")):
    if is_excluded(path):
        continue

    try:
        lines = path.read_text(errors="replace").splitlines()
    except Exception:
        continue

    for i, line in enumerate(lines):
        for pattern in INTENT_SIGNALS:
            if re.search(pattern, line):
                matches.append((path, i, line, pattern))
                break

for path, i, line, pattern in matches:
    print(f"\n--- {path}:{i + 1} ---")
    print(f"Signal: {pattern}")
    for n, text in enumerate(context(
        path.read_text(errors="replace").splitlines(),
        i,
    ), start=max(1, i - 5 + 1)):
        print(f"{n}: {text}")

print()
print("=== CANDIDATE CLASSIFICATION ===")

by_class = {}

for path, i, line, pattern in matches:
    try:
        lines = path.read_text(errors="replace").splitlines()
        body = "\n".join(context(lines, i, 12))
    except Exception:
        body = ""

    classification = classify(path, body)
    by_class.setdefault(classification, []).append(
        f"{path}:{i + 1}"
    )

for classification, locations in by_class.items():
    print(f"\n[{classification}]")
    for location in sorted(set(locations)):
        print(f"  {location}")

print()
print("=== UNAUTHORIZED-CANDIDATE CHECK ===")

authorized_gateway = []
runtime_internal = []
downstream = []
unclassified = []

for classification, locations in by_class.items():
    if classification == "AUTHORIZED GATEWAY":
        authorized_gateway.extend(locations)
    elif classification == "RUNTIME INTERNAL / COMPATIBILITY":
        runtime_internal.extend(locations)
    elif classification in {
        "PIPELINE / DOWNSTREAM",
        "DEVELOPMENT CONSTRUCTION / DOWNSTREAM",
        "IMPROVEMENT CONTROL LOOP",
    }:
        downstream.extend(locations)
    else:
        unclassified.extend(locations)

print(f"Authorized Gateway signals: {len(set(authorized_gateway))}")
print(f"Runtime internal signals:    {len(set(runtime_internal))}")
print(f"Downstream signals:           {len(set(downstream))}")
print(f"Unclassified candidates:      {len(set(unclassified))}")

if unclassified:
    print("\n[OBSERVE] Unclassified development-intent candidates require review:")
    for location in sorted(set(unclassified)):
        print(f"  {location}")
else:
    print("\n[PASS] No unclassified development-intent candidates found.")

print()
print("=== AUTHORITY CLOSURE RULES ===")
print("[RULE] FactoryAuthorityGateway is the external development-ingress authority.")
print("[RULE] Runtime development submission remains an internal compatibility seam.")
print("[RULE] Pipeline remains the development-processing owner.")
print("[RULE] Internal improvement/control-loop callers must not be migrated merely for convergence.")
print("[RULE] Existing-task execution paths are not development ingress.")
print("[RULE] Do not duplicate discovery, translation, planning, tracking, or approval in Gateway.")
print("[RULE] Any genuinely external development-intent path bypassing Gateway requires separate authority analysis.")

print()
print("=== AUTHORITY CLOSURE DECISION ===")

if unclassified:
    print("[REVIEW REQUIRED] Potential development-intent paths remain unclassified.")
    print("No production migration performed.")
else:
    print("[PASS] Development-intent authority appears closed at the current production-code level.")
    print("No production migration required by this audit.")

print()
print("=== READ-ONLY RESULT ===")
print("PASS")
print("No files were modified.")
print("No files were staged.")
print("No commit was created.")
print()
print("Return the complete output here.")
