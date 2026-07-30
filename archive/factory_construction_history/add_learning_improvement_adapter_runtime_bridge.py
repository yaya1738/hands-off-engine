from pathlib import Path

path = Path("ai/factory/runtime.py")

source = path.read_text()

if "from ai.factory.learning_improvement_adapter import FactoryLearningImprovementAdapter" not in source:
    anchor = "from ai.factory.learning_loop import FactoryLearningLoop\n"
    source = source.replace(
        anchor,
        anchor + "from ai.factory.learning_improvement_adapter import FactoryLearningImprovementAdapter\n",
        1
    )

if "self.learning_improvement_adapter =" not in source:
    anchor = "        self.learning_loop = FactoryLearningLoop()\n"
    source = source.replace(
        anchor,
        anchor + "        self.learning_improvement_adapter = FactoryLearningImprovementAdapter(self.learning_loop)\n",
        1
    )

path.write_text(source)

print({
    "status": "LEARNING_IMPROVEMENT_ADAPTER_WIRED",
    "target": str(path),
})
