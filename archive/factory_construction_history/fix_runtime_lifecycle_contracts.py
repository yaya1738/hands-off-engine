from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

text = text.replace(
"""        return {
            "status": "STARTED"
        }
""",
"""        return {
            "status": "RUNNING"
        }
""",
1,
)

text = text.replace(
"""    def run(self, payload):
        return self.execute(payload)
""",
"""    def run(self, payload):
        result = self.execute(payload)

        return {
            "cycle": 1,
            "result": result,
        }
""",
1,
)

marker = """    def stop(self):
"""

heartbeat = """
    def heartbeat(self):
        return {
            "status": "HEALTHY"
        }


"""

if "def heartbeat(self):" not in text:
    text = text.replace(marker, heartbeat + marker, 1)

# restore start visibility in public history
text = text.replace(
"""                "runtime_started",
""",
"""                "runtime_started",
""",
)

text = text.replace(
"""            if entry.get("type")
            not in {
                "integrity_report",
                "runtime_started",
                "runtime_stopped",
            }
""",
"""            if entry.get("type")
            not in {
                "integrity_report",
                "runtime_stopped",
            }
""",
1,
)

path.write_text(text)

print({
    "status": "RUNTIME_LIFECYCLE_CONTRACTS_FIXED",
    "target": "ai/factory/runtime.py"
})
