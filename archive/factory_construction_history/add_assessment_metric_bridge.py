from pathlib import Path

p = Path("ai/factory/runtime.py")

text = p.read_text()

if "def get_assessment_metrics" in text:
    print("ALREADY EXISTS")
    raise SystemExit

marker = "    def execute("

method = '''
    def get_assessment_metrics(self):
        metrics = self.observability.metrics

        if not metrics:
            return {
                "success_rate": 0,
                "average_impact": 0,
            }

        successes = [
            m.get("success", False)
            for m in metrics
            if isinstance(m, dict)
        ]

        impacts = [
            m.get("average_impact", 0)
            for m in metrics
            if isinstance(m, dict)
        ]

        return {
            "success_rate": (
                sum(successes) / len(successes)
                if successes else 0
            ),
            "average_impact": (
                sum(impacts) / len(impacts)
                if impacts else 0
            ),
        }

'''

if marker not in text:
    print("EXECUTE MARKER NOT FOUND")
    raise SystemExit

text = text.replace(marker, method + marker)

p.write_text(text)

print("UPDATED")
