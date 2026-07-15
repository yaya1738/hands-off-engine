class IntelligencePatternComparator:

    def compare(self, stored, current):

        previous = stored.get("occurrences", 0)
        current_count = current.get("occurrences", 0)

        if current.get("pattern_id") == stored.get("pattern_id"):

            return {
                "comparison": "pattern_repeated",
                "previous_occurrences": previous,
                "current_occurrences": current_count,
                "trend": "persistent",
                "mode": "read_only",
            }

        return {
            "comparison": "new_pattern",
            "previous_occurrences": previous,
            "current_occurrences": current_count,
            "trend": "new",
            "mode": "read_only",
        }
