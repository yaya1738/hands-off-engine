from ai.factory.authority_gateway import FactoryAuthorityGateway


class FactoryRuntimeAutonomyGateway:
    """Compatibility adapter whose execution path is the Authority Gateway."""

    def __init__(self):
        self.authority = FactoryAuthorityGateway()

    def evaluate(self, objective):
        """Execute through the single supported Factory execution ingress."""
        return self.authority.execute(objective)
