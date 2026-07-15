from ai.factory.planning_intelligence import (
    FactoryPlanningIntelligence,
)


def build():
    return FactoryPlanningIntelligence()


def test_create_plan():
    engine = build()

    result = engine.create_plan(
        {}
    )

    assert result["created"] is True


def test_analyze_constraints():
    engine = build()

    result = engine.analyze_constraints(
        {}
    )

    assert result["analyzed"] is True


def test_allocate_resources():
    engine = build()

    result = engine.allocate_resources(
        {}
    )

    assert result["allocated"] is True


def test_evaluate_plan():
    engine = build()

    result = engine.evaluate_plan(
        {}
    )

    assert result["evaluated"] is True


def test_history():
    engine = build()

    engine.create_plan(
        {}
    )

    assert len(engine.history()) == 1
