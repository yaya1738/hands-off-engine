from ai.factory import improvement_orchestrator as orchestrator_module


class FakeAssessor:
    def assess(self, metrics):
        return {
            "health": 1.0,
            "gaps": [],
            "objective": metrics.get("objective"),
            "interaction_health": {"available": True},
        }


class FakePlanner:
    def plan(self, assessment):
        return {"tasks": [], "priority": 0}


class FakeQueue:
    def enqueue(self, item):
        return item


class FakePublisher:
    def __init__(self):
        self.assessments = []

    def publish(self, assessment):
        self.assessments.append(assessment)
        return {"status": "sent"}


def test_orchestrator_defaults_to_assessment_bus_publisher(monkeypatch):
    publisher = FakePublisher()
    monkeypatch.setattr(
        orchestrator_module,
        "FactoryAssessmentBusPublisher",
        lambda: publisher,
    )

    orchestrator = orchestrator_module.FactoryImprovementOrchestrator(
        assessor=FakeAssessor(),
        planner=FakePlanner(),
        queue=FakeQueue(),
    )

    result = orchestrator.run_cycle({"objective": "observe"})

    assert orchestrator.assessment_publisher is publisher
    assert publisher.assessments == [result["assessment"]]
