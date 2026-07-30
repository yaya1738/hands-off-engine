from pathlib import Path

p = Path("ai/factory/runtime.py")

text = p.read_text()

marker = "    def execute("

if "def record_execution_metric" not in text:
    insert = '''
    def record_execution_metric(self, result):
        self.observability.record_metric(
            {
                "type": "execution",
                "success": bool(
                    result.get("success")
                    if isinstance(result, dict)
                    else False
                ),
                "result_type": type(result).__name__,
            }
        )

'''
    text = text.replace(marker, insert + marker)

p.write_text(text)

print("UPDATED")
