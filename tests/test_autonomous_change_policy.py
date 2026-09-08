from tools.factory_forensics.autonomous_change_policy import evaluate_change


def test_preauthorized_change_is_allowed_for_bounded_code_and_tests():
    decision = evaluate_change(
        ["ai/factory/example.py", "tests/test_example.py"],
        additions=120,
        deletions=30,
    )
    assert decision.permitted is True
    assert decision.reasons == ()


def test_preauthorized_policy_rejects_workflow_state_and_financial_surface():
    decision = evaluate_change(
        [
            "ai/factory/example.py",
            ".github/workflows/production-deploy.yml",
            "state/autonomy_liveness.json",
            "tools/polymarket_executor.py",
        ],
        additions=20,
        deletions=2,
    )
    assert decision.permitted is False
    assert any(".github" in reason for reason in decision.reasons)
    assert any("state" in reason for reason in decision.reasons)
    assert any("semantic" in reason for reason in decision.reasons)


def test_preauthorized_policy_rejects_oversized_changes():
    decision = evaluate_change(
        [f"ai/factory/module_{index}.py" for index in range(9)],
        additions=601,
        deletions=251,
    )
    assert decision.permitted is False
    assert any("file count" in reason for reason in decision.reasons)
    assert any("additions" in reason for reason in decision.reasons)
    assert any("deletions" in reason for reason in decision.reasons)
