"""Authority adapter for autonomous coordination requests."""

from ai.factory.authority_gateway import FactoryAuthorityGateway


class FactoryCoordinationAuthority:
    """Route coordination-triggered autonomous improvement through Factory authority."""

    def __init__(self, authority=None):
        self.authority = authority or FactoryAuthorityGateway()

    def trigger_self_improvement(self, context="Improve system"):
        return self.authority.execute_autonomous(
            "Run the Factory self-improvement cycle for this coordination context: "
            f"{context}"
        )
