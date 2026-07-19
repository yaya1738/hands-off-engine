from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

old = """        self.registry = FactoryRegistry()
"""

new = """        self.registry = FactoryRegistry()

        self.autonomy = FactoryAutonomyManager(
            self
        )
"""

if old not in text:
    raise SystemExit("registry initialization not found")

if "self.autonomy = FactoryAutonomyManager" not in text:
    text = text.replace(old, new, 1)

path.write_text(text)

print("autonomy manager initialized")
