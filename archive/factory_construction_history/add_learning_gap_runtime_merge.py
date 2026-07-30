from pathlib import Path

path = Path("ai/factory/runtime.py")

source = path.read_text()

old = """        translated_findings = self.development_translator.translate(
            result
        )

        development_result = self.development_pipeline.process(
            {
                "gaps": (
                    assessment_gaps
                    + translated_findings.get(
                        "gaps",
                        [],
                    )
                )
            }
        )
"""

new = """        translated_findings = self.development_translator.translate(
            result
        )

        learning_gaps = []

        if hasattr(self, "learning_improvement_adapter"):
            learning_assessment = (
                self.learning_improvement_adapter.generate_gap_assessment()
            )

            learning_gaps = learning_assessment.get(
                "gaps",
                [],
            )

        combined_gaps = (
            assessment_gaps
            + translated_findings.get(
                "gaps",
                [],
            )
            + learning_gaps
        )

        development_result = self.development_pipeline.process(
            {
                "gaps": combined_gaps
            }
        )
"""

if "learning_gaps = []" in source:
    print({"status": "ALREADY_PATCHED"})
    raise SystemExit

if old not in source:
    print({"status": "ANCHOR_NOT_FOUND"})
    raise SystemExit

source = source.replace(old, new, 1)

path.write_text(source)

print({
    "status": "LEARNING_GAPS_MERGED_INTO_DEVELOPMENT",
    "target": str(path),
})
