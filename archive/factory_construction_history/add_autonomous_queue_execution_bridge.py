from pathlib import Path

p = Path("ai/factory/runtime.py")

text = p.read_text()

if "def execute_autonomous_improvements" in text:
    print({"status": "ALREADY_EXISTS"})
    raise SystemExit

marker = "\n    def history(self):"

method = '''
    def execute_autonomous_improvements(self, cycle_result):
        executed = []

        queue = cycle_result.get("queued", [])

        for item in queue:
            if hasattr(self, "improvement_executor"):
                result = self.improvement_executor.execute(
                    item
                )
                executed.append(result)

        return {
            "executed": executed,
            "count": len(executed)
        }

'''

if marker not in text:
    print({
        "status": "ERROR",
        "reason": "history marker not found"
    })
    raise SystemExit

text = text.replace(
    marker,
    "\n" + method + marker
)

p.write_text(text)

print({
    "status": "PATCHED",
    "target": "ai/factory/runtime.py",
    "next_action": "VERIFY_COMPILE"
})
