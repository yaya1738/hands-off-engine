from pathlib import Path

for p in Path("ai/factory").rglob("*.py"):
    text = p.read_text(errors="ignore").lower()
    if "registry" in p.name.lower() or "action" in text and "register" in text:
        print(p)
