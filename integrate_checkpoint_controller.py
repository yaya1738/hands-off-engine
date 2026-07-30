from pathlib import Path

p = Path("ai/factory/runtime.py")
text = p.read_text()

method = '''
    def run_checkpoint_cycle(self):
        decision = self.checkpoint_manager.evaluate()

        state = decision.get("state")

        if state == "READY_TO_COMMIT":
            execution = self.checkpoint_executor.execute(
                decision
            )

            result = {
                "state": "COMPLETE",
                "action": "CHECKPOINT_EXECUTED",
                "decision": decision,
                "execution": execution,
            }

        elif state == "REVIEW_REQUIRED":
            result = {
                "state": "COMPLETE",
                "action": "SAFE_STOP",
                "decision": decision,
            }

        elif state == "BLOCKED":
            result = {
                "state": "COMPLETE",
                "action": "BLOCKED",
                "decision": decision,
            }

        else:
            result = {
                "state": "ERROR",
                "action": "RECOVERY_REQUIRED",
                "decision": decision,
            }

        self.improvement_audit.record(
            {
                "type": "checkpoint_cycle",
                "result": result,
            }
        )

        return result
'''

if "def run_checkpoint_cycle" in text:
    raise SystemExit("run_checkpoint_cycle already exists")

anchor = "\n    def get_assessment_metrics(self):"

if anchor not in text:
    raise SystemExit("runtime insertion point missing")

text = text.replace(
    anchor,
    method + anchor,
)

p.write_text(text)

print("CHECKPOINT_CONTROLLER_INTEGRATED")
