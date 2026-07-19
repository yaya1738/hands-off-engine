from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

if "from factory_autonomous_controller import FactoryAutonomousController" not in text:
    text = text.replace(
        "from ai.factory.development_tracker import FactoryDevelopmentTracker",
        "from ai.factory.development_tracker import FactoryDevelopmentTracker\nfrom factory_autonomous_controller import FactoryAutonomousController"
    )

if "self.autonomous_controller = FactoryAutonomousController()" not in text:
    text = text.replace(
        "self.development_tracker = FactoryDevelopmentTracker()",
        "self.development_tracker = FactoryDevelopmentTracker()\n        self.autonomous_controller = FactoryAutonomousController()"
    )

old = """def execute(self, goal):
        submitted = self.submit_goal(goal)"""

new = """def execute(self, goal):

        readiness = self.autonomous_controller.evaluate_and_execute(
            goal
        )

        if readiness.get("action") == "construction_required":
            return {
                "success": False,
                "status": "factory_not_ready",
                "readiness": readiness,
            }

        submitted = self.submit_goal(goal)"""

if old in text and "readiness = self.autonomous_controller.evaluate_and_execute" not in text:
    text = text.replace(old, new)

path.write_text(text)

print("runtime autonomous gate patch applied")
