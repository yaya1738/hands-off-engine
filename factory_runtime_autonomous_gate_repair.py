from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

text = text.replace(
    "from factory_autonomous_controller import FactoryAutonomousController\n",
    ""
)

text = text.replace(
    "        self.autonomous_controller = FactoryAutonomousController()\n",
    ""
)

text = text.replace(
"""    def execute(self, goal):

        readiness = self.autonomous_controller.evaluate_and_execute(
            goal
        )

        if readiness.get("action") == "construction_required":
            return {
                "success": False,
                "status": "factory_not_ready",
                "readiness": readiness,
            }

        submitted = self.submit_goal(goal)""",
"""    def execute(self, goal):
        submitted = self.submit_goal(goal)"""
)

path.write_text(text)

print("removed circular runtime dependency")
