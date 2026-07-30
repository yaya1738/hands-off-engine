class FactoryGapRepairController:
    """
    Autonomous capability repair coordinator.

    Receives detected Factory gaps,
    selects minimal repair paths,
    and returns repair decisions.
    """

    def __init__(self):
        self.history = []

    def analyze_gap(self, gap):
        result = {
            "gap": gap,
            "action": self.select_repair(gap)
        }

        self.history.append(result)

        return result

    def select_repair(self, gap):
        known = {
            "QUEUE_TO_DEVELOPMENT_PIPELINE":
                "CONNECT_EXISTING_PIPELINE",
            "LEARNING_TO_METRIC":
                "ADD_METRIC_BRIDGE",
        }

        return known.get(
            gap,
            "DISCOVER_REPAIR"
        )
