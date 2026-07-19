from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

marker = "class FactoryRuntime:"

insert = """
from ai.factory.autonomy_manager import (
    FactoryAutonomyManager
)

"""

if "FactoryAutonomyManager" not in text:
    text = text.replace(
        marker,
        insert + marker
    )

path.write_text(text)

print("autonomy manager import added")
