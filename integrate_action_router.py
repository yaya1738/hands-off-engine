from pathlib import Path

path = Path("ai/factory/runtime.py")
text = path.read_text()

changes = 0

if "from ai.factory.action_router import FactoryActionRouter" not in text:
    anchor = "from ai.factory.execution_handoff_adapter import FactoryExecutionHandoffAdapter\n"
    if anchor not in text:
        raise SystemExit("Import anchor missing")
    text = text.replace(
        anchor,
        anchor + "from ai.factory.action_router import FactoryActionRouter\n",
        1,
    )
    changes += 1

if "self.action_router = FactoryActionRouter(" not in text:
    anchor = """        self.execution = FactoryExecutionIntelligence()
        self.execution_handoff = FactoryExecutionHandoffAdapter()
"""
    replacement = """        self.execution = FactoryExecutionIntelligence()
        self.execution_handoff = FactoryExecutionHandoffAdapter()

        self.action_router = FactoryActionRouter(
            recovery=self.self_healing,
            improvement=self.trigger_improvement_pipeline,
        )
"""
    if anchor not in text:
        raise SystemExit("Init anchor missing")
    text = text.replace(anchor, replacement, 1)
    changes += 1

if "def trigger_improvement_pipeline" not in text:
    anchor = "    def submit_development_request(\n"
    method = """    def trigger_improvement_pipeline(self):
        return self.submit_development_request(
            "adaptive improvement request",
            "generated from adaptive decision",
        )

"""
    if anchor not in text:
        raise SystemExit("Method anchor missing")
    text = text.replace(anchor, method + anchor, 1)
    changes += 1

if 'decision["routed_action"]' not in text:
    anchor = """            decision = self.decision.create_decision(simulation)
            decision["adaptive_decision"] = adaptive_decision
            steps.append("decision")
"""
    replacement = """            decision = self.decision.create_decision(simulation)
            decision["adaptive_decision"] = adaptive_decision

            decision["routed_action"] = self.action_router.route(
                adaptive_decision
            )

            steps.append("decision")
"""
    if anchor not in text:
        raise SystemExit("Decision anchor missing")
    text = text.replace(anchor, replacement, 1)
    changes += 1

path.write_text(text)

print(f"ACTION_ROUTER_PATCH_COMPLETE changes={changes}")
