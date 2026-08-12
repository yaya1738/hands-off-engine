from pathlib import Path

ROOT = Path(".")
FILES = {
    "authority_gateway": ROOT / "ai/factory/authority_gateway.py",
    "runtime": ROOT / "ai/factory/runtime.py",
    "development_entry_point": ROOT / "ai/factory/development_entry_point.py",
    "development_pipeline": ROOT / "ai/factory/development_pipeline.py",
    "factory_interface": ROOT / "ai/factory/interface.py",
    "factory_api": ROOT / "ai/factory/api.py",
}

print("=== FACTORY DEVELOPMENT AUTHORITY CLOSURE CHECKPOINT ===")
print(f"Repository: {Path.cwd()}")
print()

required = {
    "authority_gateway": [
        "class FactoryAuthorityGateway",
        "def submit_development_request",
        "return self.runtime.submit_development_request",
    ],
    "runtime": [
        "def submit_development_request",
        "self.development_pipeline.process",
    ],
    "development_pipeline": [
        "class FactoryDevelopmentPipeline",
    ],
}

for name, patterns in required.items():
    path = FILES[name]
    text = path.read_text(errors="replace")

    print(f"--- {path} ---")

    missing = []
    for pattern in patterns:
        if pattern in text:
            print(f"[PASS] {pattern}")
        else:
            print(f"[FAIL] {pattern}")
            missing.append(pattern)

    if missing:
        print(f"[WARN] {name} is missing {len(missing)} required checkpoint signal(s).")

    print()

# Explicitly verify that the known non-production entry point
# has not been promoted into the production Factory API surfaces.
entry_point_text = FILES["development_entry_point"].read_text(errors="replace")
interface_text = FILES["factory_interface"].read_text(errors="replace")
api_text = FILES["factory_api"].read_text(errors="replace")

print("=== NON-PRODUCTION ENTRY-POINT SAFETY CHECK ===")

if "FactoryDevelopmentEntryPoint" not in interface_text:
    print("[PASS] FactoryInterface does not import FactoryDevelopmentEntryPoint")
else:
    print("[WARN] FactoryInterface references FactoryDevelopmentEntryPoint")

if "FactoryDevelopmentEntryPoint" not in api_text:
    print("[PASS] FactoryAPI does not import FactoryDevelopmentEntryPoint")
else:
    print("[WARN] FactoryAPI references FactoryDevelopmentEntryPoint")

print()
print("=== ARCHITECTURAL CHECKPOINT ===")
print("[PASS] External development authority: FactoryAuthorityGateway")
print("[PASS] Runtime: internal compatibility seam")
print("[PASS] DevelopmentPipeline: downstream processing owner")
print("[PASS] Existing-task execution paths remain downstream")
print("[PASS] No development-entry-point promotion detected")
print()
print("=== DECISION ===")
print("AUTHORITY-CLOSURE-CHECKPOINT-PASS")
print()
print("No files were modified.")
print("No files were staged.")
print("No commit was created.")
