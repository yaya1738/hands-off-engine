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


def test_persistent_strategic_objective_recurs_after_exhaustion():
    loop = FactoryAutonomousObjectiveLoop()
    objective = "keep improving autonomous capability"
    result = loop.select_next(
        {
            "strategic_objective": objective,
            "excluded_objectives": [objective],
        }
    )

    assert result["status"] == "selected"
    assert result["selected"]["objective"] == objective
    assert result["selected"]["source"] == "strategic_objective"
    assert "recurrence" in result["selected"]["reason"]
