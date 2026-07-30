from pathlib import Path

# job_runner cleanup
p = Path("ai/factory/job_runner.py")
text = p.read_text()

text = text.replace(
"""    def __init__(
        self,
        executor: Any,
    ):
        self.executor = executor
        self._history: List[Dict[str, Any]] = []
""",
"""    def __init__(self):
        self._history: List[Dict[str, Any]] = []
"""
)

p.write_text(text)


# development_orchestrator cleanup
p = Path("ai/factory/development_orchestrator.py")
text = p.read_text()

text = text.replace(
"from ai.factory.development_executor import FactoryDevelopmentExecutor\n\n",
""
)

text = text.replace(
"""    def __init__(self, executor=None):
        self.tasks: List[Dict[str, Any]] = []
        self.executor = executor
        self._history: List[Dict[str, Any]] = []
""",
"""    def __init__(self):
        self.tasks: List[Dict[str, Any]] = []
        self._history: List[Dict[str, Any]] = []
"""
)

p.write_text(text)

print("authority cleanup patch applied")
