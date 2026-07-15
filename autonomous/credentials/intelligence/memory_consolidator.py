class IntelligenceMemoryConsolidator:

    def consolidate(self, reports):

        signals = [
            r.get("signal")
            for r in reports
            if r.get("signal")
        ]

        dominant = (
            max(set(signals), key=signals.count)
            if signals else None
        )

        return {
            "memory_id": "intel_cycle_001",
            "observations": len(reports),
            "dominant_signal": dominant,
            "confidence_history": [
                r["confidence"]
                for r in reports
            ],
            "mode": "read_only",
        }
