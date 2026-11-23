from scripts.github_command_bridge import _parse


def test_parse_accepts_allowlisted_read_only_action():
    parsed = _parse("[factory-command]\nidempotency_key=regression-1\nobjective=inspect bus\naction=bus_summary")
    assert parsed is not None
    assert parsed[0]["action"] == "bus_summary"


def test_parse_rejects_execution_action():
    assert _parse("[factory-command]\nidempotency_key=regression-2\nobjective=execute work\naction=execute") is None


def test_read_file_fact_requires_path():
    assert _parse("[factory-command]\nidempotency_key=regression-3\nobjective=inspect file\naction=read_file_fact") is None


def test_read_file_fact_preserves_bounded_params():
    parsed = _parse("[factory-command]\nidempotency_key=regression-4\nobjective=inspect worker\naction=read_file_fact\nfile_path=scripts/task_worker.py\nfact=class")
    assert parsed[1] == {"file_path": "scripts/task_worker.py", "fact": "class"}


def test_parse_preserves_explicit_next_action():
    parsed = _parse("[factory-command]\nidempotency_key=regression-5\nobjective=inspect lifecycle\naction=lifecycle_summary\nnext_action_action=bus_summary")
    assert parsed is not None
    assert parsed[0]["next_action_action"] == "bus_summary"
