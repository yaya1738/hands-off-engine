class CredentialInvestigationPlanner:

    PRIORITIES = {
        "authorization_completion_confirmation": 100,
        "oauth_callback_record": 90,
        "provider_response": 80,
        "general_health_history": 50,
    }


    def plan(self, missing_evidence):

        investigations = []

        for item in missing_evidence:

            investigations.append(
                {
                    "investigation":
                    item,

                    "priority":
                    self.PRIORITIES.get(
                        item,
                        10
                    ),

                    "mode":
                    "read_only"
                }
            )

        return sorted(
            investigations,
            key=lambda x:
            x["priority"],
            reverse=True
        )
