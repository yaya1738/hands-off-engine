from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

needle = "        self.improvement_action_resolver = FactoryImprovementActionResolver()"

insert = '''
        self.improvement_action_resolver.register_action(
            "address low success rate",
            self.default_improvement_action,
        )

        self.improvement_action_resolver.register_action(
            "address low improvement impact",
            self.default_improvement_action,
        )

        self.improvement_action_resolver.register_action(
            "generic_improvement",
            self.default_improvement_action,
        )
'''

if needle in text and "address low success rate" not in text:
    text = text.replace(
        needle,
        needle + insert
    )

path.write_text(text)

print({
    "status": "PERSISTENT_ACTIONS_REGISTERED"
})
