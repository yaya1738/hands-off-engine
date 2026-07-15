class IntelligenceTimelineBuilder:

    def build(self, records):

        decisions = [
            record["decision"]
            for record in records
        ]

        risks = [
            record["risk"]
            for record in records
        ]

        return {
            "events": len(records),
            "decisions": decisions,
            "risks": risks,
            "latest_confidence": records[-1]["confidence"]
                if records else None,
            "mode": "read_only",
        }
