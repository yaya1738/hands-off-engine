import json
from pathlib import Path

from ai.ho_policy_v2_adapter import adapt_policy_v2


def test_policy_v2_adapter_generates_executor_contract(tmp_path):
    state_dir = Path(tmp_path)

    policy_v2 = {
        "generated_at": "2026-07-15T00:00:00Z",
        "weighted_recommendations": [
            {
                "action": "maintain_strategy",
                "weight": 0.85
            }
        ],
        "confidence": 0.87,
        "risk_assessment": "low"
    }

    with open(state_dir / "brain_policy_v2.json", "w") as f:
        json.dump(policy_v2, f)

    result = adapt_policy_v2(state_dir)

    assert result["status"] == "ok"

    output = state_dir / "brain_policy_next.json"
    assert output.exists()

    with open(output) as f:
        adapted = json.load(f)

    assert adapted["mode"] == "DRYRUN"
    assert adapted["source"] == "policy_brain_v2_adapter"
    assert len(adapted["actions"]) == 1
    assert adapted["actions"][0]["type"] == "summary"
