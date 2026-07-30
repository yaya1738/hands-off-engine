from datetime import datetime, timezone


class FactoryAuthorityPolicy:

    def __init__(self, authority_registry):
        self.authority_registry = authority_registry


    def authority_for(self, component):

        for authority, components in self.authority_registry.registry().items():

            if component in components:
                return authority

        return None


    def can_mutate(self, component):

        mutation_authorities = {
            "execution",
            "improvement",
            "decision",
            "learning",
        }

        authority = self.authority_for(component)

        return authority in mutation_authorities


    def report(self):

        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "authorities":
                self.authority_registry.registry(),
        }
