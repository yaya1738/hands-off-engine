from pathlib import Path

p = Path("ai/factory/runtime.py")

text = p.read_text()

old = '''        development = self.development_pipeline.process(
            findings
        )
'''

new = '''        development = self.development_pipeline.process(
            findings
        )

        self.improvement_audit.record(
            {
                "type": "development_pipeline_outcome",
                "result": development,
            }
        )

        self.learning_loop.record_outcome(
            {
                "type": "development_pipeline_outcome",
                "result": development,
            }
        )
'''

if old not in text:
    raise SystemExit("TARGET_BLOCK_NOT_FOUND")

if new in text:
    raise SystemExit("ALREADY_APPLIED")

p.write_text(text.replace(old, new, 1))

print("PATCH_APPLIED")
