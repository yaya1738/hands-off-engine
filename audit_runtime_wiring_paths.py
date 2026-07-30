import ast
from pathlib import Path

ROOT = Path("ai/factory")

targets = {
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
}

for file in ROOT.glob("*.py"):
    try:
        tree = ast.parse(file.read_text())
    except:
        continue

    for node in ast.walk(tree):

        # self.component = Component(...)
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    if target.attr in targets:
                        print(
                            f"{file.name}:{node.lineno}: CREATES {target.attr}"
                        )

        # component passed as keyword argument
        if isinstance(node, ast.keyword):
            if node.arg in targets:
                print(
                    f"{file.name}:{node.lineno}: INJECTS {node.arg}"
                )

        # getattr(self, "component")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id == "getattr":
                    for arg in node.args:
                        if isinstance(arg, ast.Constant):
                            if arg.value in targets:
                                print(
                                    f"{file.name}:{node.lineno}: LOOKUP {arg.value}"
                                )
