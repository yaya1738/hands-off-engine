class SupervisorIntelligence:

    def generate(self, digest):

        return {
            "component": "credential_supervisor",
            "intelligence": digest,
            "mode": "read_only",
            "actions_allowed": False,
        }
