from ai.factory.autonomous_objective_loop import FactoryAutonomousObjectiveLoop


def test_selects_highest_value_candidate_with_stable_tie_breaking():
    loop = FactoryAutonomousObjectiveLoop()
    result = loop.select_next(
        {
            "gaps": ["zeta gap", "alpha gap"],
            "findings": ["lower priority finding"],
        }
    )

    assert result["status"] == "selected"
    assert result["selected"]["objective"] == "alpha gap"
    assert result["selected"]["authority"] == "FactoryAuthorityGateway"
    assert result["selected"]["execution_permitted"] is False


def test_missing_integration_boundary_outranks_generic_gap():
    loop = FactoryAutonomousObjectiveLoop()
    result = loop.select_next(
        {
            "gaps": ["generic capability gap"],
            "discovery": {"missing": ["improvement_executor"]},
        }
    )

    assert result["selected"]["source"] == "integration_health"
    assert "improvement_executor" in result["selected"]["objective"]


def test_empty_discovery_is_non_executing_no_candidate():
    loop = FactoryAutonomousObjectiveLoop()
    result = loop.select_next({})

    assert result["status"] == "no_candidate"
    assert result["candidate_count"] == 0
    assert result["candidates"] == []
    assert result["excluded_objectives"] == []
    assert result["selected"] is None


def test_exhausted_strategic_objective_becomes_bounded_continuity_checkpoint():
    loop = FactoryAutonomousObjectiveLoop()
    objective = "keep improving autonomous capability"
    result = loop.select_next(
        {
            "strategic_objective": objective,
            "excluded_objectives": [objective],
            "cycle_count": 7,
        }
    )

    selected = result["selected"]
    assert result["status"] == "selected"
    assert selected["source"] == "autonomous_continuity"
    assert selected["reason"] == "bounded continuity objective after candidate exhaustion"
    assert "checkpoint 7" in selected["objective"]
    assert selected["strategic_objective"] == objective
    assert selected["execution_permitted"] is False


def test_continuity_checkpoint_changes_with_cycle_count():
    loop = FactoryAutonomousObjectiveLoop()
    objective = "keep improving autonomous capability"
    first = loop.select_next(
        {"strategic_objective": objective, "excluded_objectives": [objective], "cycle_count": 1}
    )["selected"]["objective"]
    second = loop.select_next(
        {"strategic_objective": objective, "excluded_objectives": [objective], "cycle_count": 2}
    )["selected"]["objective"]

    assert first != second
    assert "checkpoint 1" in first
    assert "checkpoint 2" in second
