class IntelligenceStateComparator:

    def compare(self, previous, current):

        changes = []

        for key in [
            "health",
            "stability",
            "confidence",
            "drift",
            "situation",
        ]:

            if previous.get(key) != current.get(key):
                changes.append(key)

        if len(changes) == 0:
            trend = "stable"

        elif (
            "health" in changes
            or "confidence" in changes
        ):
            trend = "degrading"

        else:
            trend = "changed"

        return {
            "trend":
                trend,

            "changes":
                changes,

            "mode":
                "read_only",
        }
