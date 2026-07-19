from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

needle = """        return result


    def report_autonomy_state"""

insert = """        return result


    def process_approved_improvement(
        self,
        improvement,
        action,
    ):
        if improvement.get("status") != "APPROVED":
            return {
                "status": "blocked",
                "reason": "improvement_not_approved",
            }

        result = self.execute_approved_improvement(
            improvement,
            action,
        )

        self.improvement_audit.record(
            {
                "type": "approved_improvement_processed",
                "result": result,
            }
        )

        return result


    def report_autonomy_state"""

if needle not in text:
    raise SystemExit("Insertion point not found")

path.write_text(text.replace(needle, insert))

print("updated")
