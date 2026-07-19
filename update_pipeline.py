from pathlib import Path

p = Path("ai/factory/development_pipeline.py")

s = p.read_text()

old = """    def __init__(self):
        self.orchestrator = FactoryDevelopmentOrchestrator()
        self.lifecycle = FactoryChangeLifecycleManager()
        self.artifact_generator = FactoryDevelopmentArtifactGenerator()
        self.artifact_registry = FactoryArtifactRegistry()
        self._history = []
"""

new = """    def __init__(self, artifact_registry=None):
        self.orchestrator = FactoryDevelopmentOrchestrator()
        self.lifecycle = FactoryChangeLifecycleManager()
        self.artifact_generator = FactoryDevelopmentArtifactGenerator()
        self.artifact_registry = (
            artifact_registry
            or FactoryArtifactRegistry()
        )
        self._history = []
"""

if old not in s:
    print("TARGET NOT FOUND")
    exit(1)

p.write_text(s.replace(old, new))
print("UPDATED")
