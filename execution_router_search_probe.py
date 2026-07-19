from pathlib import Path

for p in Path("ai/factory").rglob("*.py"):
    text = p.read_text(errors="ignore")
    if "Callable" in text and ("execute" in text or "action" in text):
        print(p)
