from ai.factory.improvement_orchestrator import (
    FactoryImprovementOrchestrator,
)
from ai.factory.self_assessment import (
    FactorySelfAssessment,
)
from ai.factory.improvement_planner import (
    FactoryImprovementPlanner,
)
from ai.factory.improvement_queue import (
    FactoryImprovementQueue,
)


def build_orchestrator():
    return FactoryImprovementOrchestrator(
        assessor=FactorySelfAssessment(),
        planner=FactoryImprovementPlanner(),
        queue=FactoryImprovementQueue(),
    )


def test_run_cycle():
    orchestrator = build_orchestrator()

    result = orchestrator.run_cycle(
        {
            "success_rate": 0.5,
        }
    )

    assert len(
        result["queued"]
    ) > 0


def test_process():
    orchestrator = build_orchestrator()

    orchestrator.run_cycle(
        {
            "success_rate": 0.5,
        }
    )

    result = orchestrator.process()

    assert result["status"] == "RUNNING"


def test_history():
    orchestrator = build_orchestrator()

    orchestrator.run_cycle(
        {
            "success_rate": 1,
        }
    )

    assert len(
        orchestrator.history()
    ) == 1
