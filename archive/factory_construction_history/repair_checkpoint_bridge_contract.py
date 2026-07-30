from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

text = text.replace(
'''                    self.checkpoint_manager.create_checkpoint(
                        {
                            "type": "autonomous_improvement",
                            "improvement": approved,
                            "result": result,
                        }
                    )
''',
'''                    checkpoint_request = {
                        "type": "autonomous_improvement",
                        "improvement": approved,
                        "result": result,
                    }

                    checkpoint_plan = self.checkpoint_manager.evaluate(
                        checkpoint_request
                    )

                    if hasattr(self, "checkpoint_executor"):
                        self.checkpoint_executor.execute(
                            checkpoint_plan
                        )
'''
)

text = text.replace(
'''                validation_result = self.improvement_assessment.assess()
''',
'''                validation_result = self.improvement_assessment.assess(
                    self.get_assessment_metrics()
                    if hasattr(self, "get_assessment_metrics")
                    else {}
                )
'''
)

path.write_text(text)

print({
    "status": "CHECKPOINT_CONTRACT_REPAIRED"
})
