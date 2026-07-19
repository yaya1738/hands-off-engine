from pathlib import Path

print("FACTORY CHANGE BOUNDARY")
print("=" * 35)

for p in Path(".").glob("*"):
    name = p.name.lower()

    if not p.is_file():
        continue

    if any(x in name for x in [
        "probe",
        "audit",
        "report",
        "test",
        "patch",
        "backup",
        "json",
        "update",
        "verify",
    ]):
        continue

    if name.startswith("factory_") or "ai" in str(p):
        print("ARCHITECTURE CANDIDATE:", p)

print("DONE")
