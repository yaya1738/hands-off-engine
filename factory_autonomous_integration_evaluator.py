import json
from datetime import datetime, timezone


EXPECTED_ACTIONS = {
    "activate_existing_lifecycle",
    "request_factory_build",
}


class FactoryAutonomousIntegrationEvaluator:

    def evaluate(self, controller_output):

        decision = controller_output.get(
            "decision",
            {}
        )

        action = decision.get(
            "action"
        )

        capabilities = controller_output.get(
            "capabilities",
            {}
        )

        missing = decision.get(
            "missing",
            []
        )

        if action in EXPECTED_ACTIONS:

            if action == "activate_existing_lifecycle":
                return {
                    "status": "PASS",
                    "classification": "factory_ready",
                    "next_action": "continue_activation"
                }

            if action == "request_factory_build":
                return {
                    "status": "BUILD_REQUIRED",
                    "classification": "missing_capability",
                    "missing": missing,
                    "next_action": "send_to_factory_construction"
                }


        # Detect inspection-style output
        if len(controller_output.keys()) > 6:

            return {
                "status": "WARNING",
                "classification": "inspection_output_detected",
                "next_action": "compress_to_decision_layer"
            }


        return {
            "status": "FAILED",
            "classification": "unknown_factory_state",
            "next_action": "investigate"
        }



def run():

    # Example placeholder.
    # Later this imports the controller directly.
    sample = {
        "decision": {
            "action": "activate_existing_lifecycle",
            "missing": []
        },
        "capabilities": {
            "authority_gateway": True,
            "construction_pipeline": True,
            "completion_adapter": True,
            "artifact_registry": True
        }
    }


    evaluator = FactoryAutonomousIntegrationEvaluator()

    return {
        "timestamp":
            datetime.now(timezone.utc).isoformat(),

        "component":
            "factory_autonomous_integration_evaluator",

        "evaluation":
            evaluator.evaluate(sample)
    }


if __name__ == "__main__":
    print(
        json.dumps(
            run(),
            indent=2
        )
    )
