from factory_autonomous_controller import FactoryAutonomousController


class FactoryRuntimeAutonomyGateway:

    def __init__(self):
        self.controller = FactoryAutonomousController()

    def evaluate(self, objective):
        return self.controller.evaluate_and_execute(
            objective
        )
