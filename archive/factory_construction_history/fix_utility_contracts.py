from pathlib import Path


# ---------- Event Bus ----------
path = Path("ai/factory/event_bus.py")
if path.exists():
    text = path.read_text()

    if "def publish(" not in text:
        text += '''

    def publish(
        self,
        event_type,
        payload,
    ):
        event = {
            "type": event_type,
            "payload": payload,
        }

        if not hasattr(self, "_history"):
            self._history = []

        self._history.append(event)

        for handler in getattr(
            self,
            "_subscribers",
            {},
        ).get(event_type, []):
            handler(payload)

        return event
'''

    if "_history" not in text:
        text = text.replace(
            "class FactoryEventBus:",
            "class FactoryEventBus:\n    _history = []\n"
        )

    path.write_text(text)


# ---------- Scheduler ----------
path = Path("ai/factory/scheduler.py")
if path.exists():
    text = path.read_text()

    if "def schedule(" not in text:
        text += '''

    def schedule(
        self,
        job_id,
        action,
        delay,
    ):
        if not hasattr(self, "_jobs"):
            self._jobs = []

        job = {
            "id": job_id,
            "action": action,
            "delay": delay,
        }

        self._jobs.append(job)

        return job


    def run_pending(self):
        jobs = getattr(
            self,
            "_jobs",
            [],
        )

        self._jobs = []

        return jobs
'''

    path.write_text(text)


# ---------- Service ----------
path = Path("ai/factory/service.py")
if path.exists():
    text = path.read_text()

    if "def handle(" not in text:
        text += '''

    def handle(
        self,
        command,
    ):
        if command == "status":
            return self.health()

        return {
            "status": "unknown_command",
        }


    def health(self):
        return {
            "status": "healthy",
        }
'''

    path.write_text(text)


# ---------- Learning Memory ----------
path = Path("ai/factory/learning_memory.py")
if path.exists():
    text = path.read_text()

    if "def store(" not in text:
        text += '''

    def store(
        self,
        item,
    ):
        if not hasattr(self, "_memory"):
            self._memory = []

        self._memory.append(item)

        return item


    def history(self):
        return getattr(
            self,
            "_memory",
            [],
        )
'''

    path.write_text(text)


print({
    "status": "UTILITY_COMPAT_CONTRACTS_PATCHED"
})
