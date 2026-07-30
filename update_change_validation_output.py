from pathlib import Path

path = Path("ai/factory/change_validation.py")
text = path.read_text()

old = """        report = {
            "status": status,
            "checks": checks,
        }

        self._history.append(report)

        return report
"""

new = """        failed_checks = [
            name
            for name, value in checks.items()
            if not value
        ]

        report = {
            "status": status,
            "capability": "action_router_integration",
            "checks": checks,
            "failed_checks": failed_checks,
            "audit_state": (
                "READY_FOR_COMMIT"
                if status == "PASS"
                else "BLOCKED"
            ),
        }

        self._history.append(report)

        return report

    def summary(self, report):
        lines = [
            "FACTORY CHANGE VALIDATION",
            f"STATUS: {report.get('status')}",
            "",
            f"CAPABILITY: {report.get('capability')}",
            "",
            "CHECKS:",
        ]

        for name, value in report.get(
            "checks",
            {},
        ).items():
            lines.append(
                f"{'PASS' if value else 'FAIL'}  {name}"
            )

        lines.extend(
            [
                "",
                f"AUDIT STATE: {report.get('audit_state')}",
            ]
        )

        return "\\n".join(lines)
"""

if old not in text:
    raise SystemExit("Expected validator block not found")

text = text.replace(old, new, 1)

path.write_text(text)

print("CHANGE_VALIDATION_OUTPUT_UPDATED")
