"""
Hands-Off Credential Recovery Engine
"""

class CredentialRecovery:

    def recover(self, health_result):
        if health_result["healthy"]:
            return {
                "action": "none",
                "reason": "credential_healthy",
            }

        return {
            "action": "begin_recovery",
            "reason": "credential_unhealthy",
        }
