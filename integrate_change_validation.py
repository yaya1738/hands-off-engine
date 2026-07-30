from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

changes = 0

if "from ai.factory.change_validation import FactoryChangeValidation" not in text:
    anchor = "from ai.factory.improvement_capability_registry import FactoryImprovementCapabilityRegistry\n"
    if anchor not in text:
        raise SystemExit("import anchor missing")

    text = text.replace(
        anchor,
        anchor + "from ai.factory.change_validation import FactoryChangeValidation\n",
        1,
    )
    changes += 1

if "self.change_validation = FactoryChangeValidation()" not in text:
    anchor = "self.improvement_capability_registry = FactoryImprovementCapabilityRegistry()"

    if anchor not in text:
        raise SystemExit("init anchor missing")

    text = text.replace(
        anchor,
        anchor + "\n        self.change_validation = FactoryChangeValidation()",
        1,
    )
    changes += 1

if "def validate_factory_change" not in text:
    anchor = "    def submit_development_request(\n"

    method = """    def validate_factory_change(self):
        result = (
            self.change_validation
            .validate_action_router_integration()
        )

        self.improvement_audit.record(
            {
                "type": "factory_change_validation",
                "result": result,
            }
        )

        return result

"""

    if anchor not in text:
        raise SystemExit("method anchor missing")

    text = text.replace(
        anchor,
        method + anchor,
        1,
    )
    changes += 1

path.write_text(text)

print(f"CHANGE_VALIDATION_INTEGRATED changes={changes}")
