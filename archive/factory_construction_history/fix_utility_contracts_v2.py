from pathlib import Path


# Event Bus
path = Path("ai/factory/event_bus.py")
text = path.read_text()

if "for handler in getattr(" in text:
    text = text.replace(
'''        for handler in getattr(
            self,
            "_subscribers",
            {},
        ).get(event_type, []):
            handler(payload)
''',
'''        subscribers = getattr(
            self,
            "_subscribers",
            getattr(self, "subscribers", {}),
        )

        for handler in subscribers.get(event_type, []):
            handler(payload)
'''
)

path.write_text(text)


# Scheduler
path = Path("ai/factory/scheduler.py")
text = path.read_text()

if "def list_jobs(" not in text:
    text += '''

    def list_jobs(self):
        return getattr(
            self,
            "_jobs",
            [],
        )
'''

text = text.replace(
'''        self._jobs = []

        return jobs
''',
'''        for job in jobs:
            job["runs"] = job.get(
                "runs",
                0,
            ) + 1

        return jobs
'''
)

path.write_text(text)


# Service
path = Path("ai/factory/service.py")
text = path.read_text()

text = text.replace(
'''        if command == "status":
            return self.health()
''',
'''        if command == "status":
            return {
                "command": "status",
                **self.health(),
            }
'''
)

text = text.replace(
'''        return {
            "status": "healthy",
        }
''',
'''        return {
            "status": "running",
        }
'''
)

path.write_text(text)


# Feedback Engine
path = Path("ai/factory/feedback_engine.py")
text = path.read_text()

if "patterns" not in text:
    text = text.replace(
        "    def analyze(self):",
'''    def analyze(self):
        patterns = {}

        for item in self.memory.history():
            action = item.get("action")
            if action:
                patterns[action] = patterns.get(
                    action,
                    0,
                ) + 1

        return {
            "patterns": patterns,
        }


    def _old_analyze(self):
'''
)

text = text.replace(
'''            "recommendation": "CONTINUE_MONITORING"
''',
'''            "recommendation": (
                "OPTIMIZE_IMPROVEMENT_FLOW"
                if self.memory.history()
                else "CONTINUE_MONITORING"
            )
'''
)

path.write_text(text)


print({
    "status": "UTILITY_CONTRACTS_V2_FIXED"
})
