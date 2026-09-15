from ai.factory.improvement_planner import FactoryImprovementPlanner


def test_plan_preserves_bounded_decision_context():
    context = {"available": True, "interaction": {"correlation_rate": 0.5}, "admission": {"available": True, "msg_id": "m-1", "admitted": True}, "assessment": {"available": True, "health": 0.9}}
    plan = FactoryImprovementPlanner().plan({"health": 0.9, "objective": "improve interaction reliability", "gaps": [], "decision_context": context})
    assert plan["decision_context"] == context
    assert plan["decision_context"] is not context


def test_plan_uses_decision_context_to_raise_interaction_priority():
    planner = FactoryImprovementPlanner()
    baseline = planner.plan({"health": 0.9, "gaps": []})
    informed = planner.plan({"health": 0.9, "gaps": [], "decision_context": {"available": True, "interaction": {"correlation_rate": 0.5, "orphan_reply_count": 0, "single_event_count": 0, "task_thread_coverage": 0.5, "window_truncated": False}}})
    assert informed["priority"] > baseline["priority"]
