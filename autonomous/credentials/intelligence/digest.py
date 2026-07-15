class CredentialDigest:

    def generate(self, metrics, health):

        return {
            "system": "credential_bridge",
            "metrics": metrics,
            "health": health
        }
