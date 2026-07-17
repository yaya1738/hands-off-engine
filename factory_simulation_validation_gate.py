from datetime import datetime, timezone


class FactorySimulationValidationGate:

    def validate(self, simulation_report):

        validations = []

        for item in simulation_report.get(
            "simulations",
            []
        ):

            confidence = item.get(
                "confidence",
                0
            )

            regression = item.get(
                "regression_detected"
            )

            status = item.get(
                "simulation_status"
            )

            if (
                status == "completed"
                and regression is False
                and confidence >= 0.8
            ):
                result = {
                    "validation":
                        "passed",

                    "authorization":
                        "eligible",

                    "execution_allowed":
                        False
                }

            elif status == "deferred":

                result = {
                    "validation":
                        "pending_review",

                    "authorization":
                        "not_eligible",

                    "execution_allowed":
                        False
                }

            else:

                result = {
                    "validation":
                        "failed",

                    "authorization":
                        "blocked",

                    "execution_allowed":
                        False
                }


            validations.append(
                {
                    "component":
                        item["component"],

                    "owner":
                        item["owner"],

                    **result
                }
            )


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component":
                "factory_simulation_validation_gate",

            "validation_count":
                len(validations),

            "validations":
                validations,

            "status":
                "validation_complete"
        }
