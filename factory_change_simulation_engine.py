from datetime import datetime, timezone


class FactoryChangeSimulationEngine:

    def simulate(self, approval_report):

        simulations = []

        for decision in approval_report.get(
            "decisions",
            []
        ):

            action = decision.get(
                "decision"
            )

            if action == "approve_simulation":

                result = {
                    "component":
                        decision["component"],

                    "owner":
                        decision["owner"],

                    "simulation_status":
                        "completed",

                    "predicted_effect":
                        "positive",

                    "regression_detected":
                        False,

                    "confidence":
                        0.85,

                    "execution_recommendation":
                        "hold_for_authorization"
                }

            elif action == "request_review":

                result = {
                    "component":
                        decision["component"],

                    "owner":
                        decision["owner"],

                    "simulation_status":
                        "deferred",

                    "predicted_effect":
                        "unknown",

                    "regression_detected":
                        None,

                    "confidence":
                        0.0,

                    "execution_recommendation":
                        "review_required"
                }

            else:

                result = {
                    "component":
                        decision["component"],

                    "owner":
                        decision["owner"],

                    "simulation_status":
                        "rejected",

                    "predicted_effect":
                        "negative",

                    "regression_detected":
                        True,

                    "confidence":
                        1.0,

                    "execution_recommendation":
                        "blocked"
                }

            simulations.append(result)


        return {
            "timestamp":
                datetime.now(timezone.utc).isoformat(),

            "component":
                "factory_change_simulation_engine",

            "simulation_count":
                len(simulations),

            "simulations":
                simulations,

            "status":
                "simulation_complete"
        }
