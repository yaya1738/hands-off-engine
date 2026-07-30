from pathlib import Path

# 1. Remove DevelopmentOrchestrator executor bypass
p = Path("ai/factory/development_orchestrator.py")
text = p.read_text()

text = text.replace(
    "from ai.factory.development_executor import FactoryDevelopmentExecutor\n\n",
    ""
)

old = """    def execute_task(
        self,
        task: Dict[str, Any],
    ):
        result = self.executor.execute(
            task
        )

        self._history.append(
            result
        )

        return result
"""

new = """    def execute_task(
        self,
        task: Dict[str, Any],
    ):
        result = {
            "status": "HANDOFF_REQUIRED",
            "task": task,
            "authority": "FactoryRuntime",
        }

        self._history.append(result)

        return result
"""

if old in text:
    text = text.replace(old, new)
else:
    print("development_orchestrator execute_task block not found")

p.write_text(text)


# 2. Remove JobRunner executor bypass
p = Path("ai/factory/job_runner.py")
text = p.read_text()

old = """        result = self.executor.execute(
            job_type,
            payload,
        )
"""

new = """        result = {
            "status": "HANDOFF_REQUIRED",
            "job_type": job_type,
            "payload": payload,
            "authority": "FactoryRuntime",
        }
"""

if old in text:
    text = text.replace(old, new)
else:
    print("job_runner execute block not found")

p.write_text(text)


# 3. Remove IntelligenceCoordinator improvement bypass
p = Path("ai/factory/intelligence_coordinator.py")
text = p.read_text()

old = """            result = self.improvement.execute()
"""

new = """            result = {
                "status": "HANDOFF_REQUIRED",
                "authority": "FactoryRuntime",
            }
"""

if old in text:
    text = text.replace(old, new)
else:
    print("intelligence improvement block not found")

p.write_text(text)


print("Authority boundary patch applied")
