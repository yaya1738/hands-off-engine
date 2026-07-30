from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

needle = """        return result


    def report_autonomy_state"""

insert = """        return result


    def process_approval_pipeline(
        self,
        approval_request,
        action,
    ):
        if approval_request.get("status") != "APPROVED":
            return {
                "status": "blocked",
                "reason": "approval_not_ready",
            }

        improvement = approval_request.get(
            "improvement"
        )

        result = self.process_approved_improvement(
            improvement,
            action,
        )

        self.improvement_audit.record(
            {
                "type": "approval_pipeline_processed",
                "approval": approval_request,
                "result": result,
            }
        )

        return result


    def report_autonomy_state"""

if needle not in text:
    raise SystemExit("Insertion point not found")

path.write_text(text.replace(needle, insert))

print("updated")
