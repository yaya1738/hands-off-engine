import ast
from pathlib import Path

ROOT = Path("ai/factory")

targets = {
    "improvement_orchestrator",
    "improvement_executor",
    "strategy_manager",
    "decision_option_adapter",
    "feedback_engine",
    "learning_loop",
    "adaptive_decision",
    "checkpoint_executor",
    "execution_handoff",
    "action_router",
}

for file in ROOT.glob("*.py"):

    try:
        tree = ast.parse(file.read_text())
    except:
        continue

    for node in ast.walk(tree):

        if isinstance(node, ast.Call):

            func = node.func

            if isinstance(func, ast.Attribute):

                if isinstance(func.value, ast.Attribute):
                    if (
                        isinstance(func.value.value, ast.Name)
                        and func.value.value.id == "self"
                        and func.value.attr in targets
                    ):
                        print(
                            f"{file.name}:{node.lineno}: "
                            f"self.{func.value.attr}.{func.attr}()"
                        )

                elif isinstance(func.value, ast.Name):
                    if func.value.id in targets:
                        print(
                            f"{file.name}:{node.lineno}: "
                            f"{func.value.id}.{func.attr}()"
                        )
