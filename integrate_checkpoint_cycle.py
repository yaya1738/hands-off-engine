from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

method = '''
    def run_checkpoint_cycle(self):
        decision = self.checkpoint_manager.evaluate()

        if decision.get("state") != "READY_TO_COMMIT":
            return {
                "status": "NOT_READY",
                "decision": decision,
            }

        result = self.checkpoint_executor.execute(
            decision
        )

        self.improvement_audit.record(
            {
                "type": "checkpoint_cycle",
                "result": result,
            }
        )

        return {
            "status": "COMPLETE",
            "decision": decision,
            "execution": result,
        }
'''

if "def run_checkpoint_cycle" not in text:
    anchor = "\n    def get_assessment_metrics(self):"

    if anchor not in text:
        raise SystemExit("runtime anchor not found")

    text = text.replace(
        anchor,
        method + anchor,
    )

p.write_text(text)

print("CHECKPOINT_CYCLE_INTEGRATED")
