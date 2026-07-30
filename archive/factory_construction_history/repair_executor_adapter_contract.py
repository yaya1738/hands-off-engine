from pathlib import Path
import re

runtime = Path("ai/factory/runtime.py")
text = runtime.read_text()

old = """result = self.improvement_executor.execute(
                    item
                )"""

new = """result = self.improvement_executor.execute(
                    item,
                    item
                )"""

if old in text:
    text = text.replace(old, new)
    runtime.write_text(text)
    print({
        "status": "PATCHED",
        "change": "executor_adapter_contract"
    })
else:
    print({
        "status": "NOT_FOUND",
        "reason": "adapter call pattern changed"
    })
