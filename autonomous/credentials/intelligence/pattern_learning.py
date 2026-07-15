class PatternLearningEngine:

    def analyze(self, history):

        patterns = {}

        for item in history:
            key = item.get("diagnosis")

            if key not in patterns:
                patterns[key] = {
                    "occurrences": 0,
                    "resolved": 0,
                }

            patterns[key]["occurrences"] += 1

            if item.get("outcome") == "resolved":
                patterns[key]["resolved"] += 1

        for key, value in patterns.items():
            total = value["occurrences"]

            value["reliability"] = (
                value["resolved"] / total
                if total
                else 0
            )

        return patterns


    def analyse(self, history):
        return self.analyze(history)
