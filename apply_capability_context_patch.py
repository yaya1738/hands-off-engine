from pathlib import Path

path = Path("ai/factory/runtime.py")

text = path.read_text()

import_line = (
    "from ai.factory.capability_evolution_context import "
    "FactoryCapabilityEvolutionContext"
)

if import_line not in text:
    anchor = "from ai.factory.capability_evolution_decision import FactoryCapabilityEvolutionDecision\n"
    if anchor not in text:
        print("IMPORT_ANCHOR_NOT_FOUND")
        raise SystemExit(1)

    text = text.replace(
        anchor,
        anchor + import_line + "\n",
        1,
    )

init_anchor = (
    "self.capability_evolution_decision = FactoryCapabilityEvolutionDecision()\n"
)

if "self.capability_evolution_context" not in text:
    if init_anchor not in text:
        print("INIT_ANCHOR_NOT_FOUND")
        raise SystemExit(1)

    text = text.replace(
        init_anchor,
        init_anchor +
        "        self.capability_evolution_context = FactoryCapabilityEvolutionContext()\n",
        1,
    )

decision_anchor = (
    """        capability_evolution_decision = (
            self.capability_evolution_decision.decide(
                capability_gap_analysis,
                capability_consolidation,
            )
        )
"""
)

context_block = (
    decision_anchor +
    """
        capability_context = (
            self.capability_evolution_context.build(
                capability_gap_analysis,
                capability_consolidation,
                capability_evolution_decision,
            )
        )
"""
)

if "capability_context = (" not in text:
    if decision_anchor not in text:
        print("DECISION_ANCHOR_NOT_FOUND")
        raise SystemExit(1)

    text = text.replace(
        decision_anchor,
        context_block,
        1,
    )

cycle_anchor = (
    '"capability_consolidation": capability_consolidation,\n'
)

if '"capability_context": capability_context,' not in text:
    if cycle_anchor not in text:
        print("CYCLE_ANCHOR_NOT_FOUND")
        raise SystemExit(1)

    text = text.replace(
        cycle_anchor,
        cycle_anchor +
        '                "capability_context": capability_context,\n',
        1,
    )

path.write_text(text)

print("CAPABILITY_CONTEXT_PATCH_APPLIED")
