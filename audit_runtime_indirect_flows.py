import ast
from pathlib import Path

ROOT = Path("ai/factory")

targets = [
    "improvement_orchestrator",
    "improvement_executor",
    "strategy_manager",
    "learning_loop",
    "feedback_engine",
    "adaptive_decision",
    "action_router",
    "checkpoint_executor",
    "execution_handoff",
    "decision_option_adapter",
]

for file in ROOT.glob("*.py"):
    try:
        tree = ast.parse(file.read_text())
    except:
        continue

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                if node.value.id in targets:
                    print(
                        f"{file.name}:{node.lineno}: "
                        f"{node.value.id}.{node.attr}"
                    )
