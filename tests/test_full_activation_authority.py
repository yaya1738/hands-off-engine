from pathlib import Path

SOURCE = Path("autonomous/full_activation.py").read_text()


def test_legacy_full_activation_has_no_process_or_remote_execution():
    forbidden = ("import subprocess", "subprocess.", "doctl", "rsync", "curl")
    assert all(token not in SOURCE for token in forbidden)


def test_legacy_operations_fail_closed():
    namespace = {"__name__": "full_activation_test"}
    exec(compile(SOURCE, "autonomous/full_activation.py", "exec"), namespace)
    activation = namespace["FullActivation"]()
    assert activation.full_activation()["disabled"] is True
    assert activation.activate_node_coordination()["disabled"] is True
    assert activation.get_status()["ready_for_capital"] is False
