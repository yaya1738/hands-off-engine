from ai.decision.convergence import ConvergenceController


def test_convergence_blocks_without_approval():
    controller = ConvergenceController()
    decision = controller.evaluate(
        action="test", confidence=0.9, risk_score=0.1,
        costs={"fee": 1}, evidence={"analysis": "ok"},
    )
    assert controller.execute(decision=decision, executor=lambda _: {"ok": True})["status"] == "blocked"


def test_convergence_executes_only_after_decision_and_verifies():
    controller = ConvergenceController()
    decision = controller.evaluate(
        action="test", confidence=0.9, risk_score=0.1,
        costs={"fee": 1}, evidence={"analysis": "ok"},
    )
    result = controller.execute(
        decision=decision,
        executor=lambda _: {"ok": True},
        verifier=lambda result, _: result.get("ok") is True,
    )
    assert result["status"] == "verified"
    assert result["verified"] is True


def test_convergence_never_treats_unverified_execution_as_verified():
    controller = ConvergenceController()
    decision = controller.evaluate(
        action="test", confidence=0.9, risk_score=0.1,
        costs={"fee": 1}, evidence={"analysis": "ok"},
    )
    result = controller.execute(
        decision=decision,
        executor=lambda _: {"ok": True},
        verifier=lambda *_: False,
    )
    assert result["status"] == "verification_failed"
