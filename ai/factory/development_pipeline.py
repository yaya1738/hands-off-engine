from typing import Any, Dict, Optional

from ai.factory.development_orchestrator import FactoryDevelopmentOrchestrator
from ai.factory.change_lifecycle_manager import FactoryChangeLifecycleManager
from ai.factory.development_artifact_generator import FactoryDevelopmentArtifactGenerator
from ai.factory.development_executor import FactoryDevelopmentExecutor
from ai.factory.artifact_registry import FactoryArtifactRegistry


class FactoryDevelopmentPipeline:

    def __init__(self, artifact_registry=None, local_agent: Optional[Any] = None):
        self.executor = FactoryDevelopmentExecutor(local_agent=local_agent)
        self.orchestrator = FactoryDevelopmentOrchestrator(executor=self.executor)
        self.lifecycle = FactoryChangeLifecycleManager()
        self.artifact_generator = FactoryDevelopmentArtifactGenerator()
        self.artifact_registry = artifact_registry or FactoryArtifactRegistry()
        self._history = []

    def run_development_cycle(self, task: Dict[str, Any]):
        development_task = self.orchestrator.create_development_task(task)
        artifact = self.artifact_generator.generate(
            task.get("objective") or task.get("goal") or "factory_development_task",
            development_task,
            task,
        )
        self.artifact_registry.register_artifact(
            artifact["artifact_id"],
            artifact.get("task_id"),
            artifact["type"],
            artifact["location"],
        )
        execution = self.orchestrator.execute_task(task)
        change = self.lifecycle.start_change(task)
        validation = self.lifecycle.validate_change(task)
        self.artifact_registry.complete_artifact(
            artifact["artifact_id"],
            {"execution": execution, "change": change, "validation": validation},
        )
        result = {
            "task": development_task,
            "artifact": artifact,
            "execution": execution,
            "change": change,
            "validation": validation,
            "status": "ready_for_review",
        }
        self._history.append(result)
        return result

    def process(self, findings: Dict[str, Any]):
        return self.run_development_cycle(findings)

    def report(self):
        return {
            "cycles": len(self._history),
            "history": self._history,
            "artifacts": self.artifact_registry.list_artifacts(),
        }
