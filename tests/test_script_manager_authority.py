"""Regression coverage for the quarantined ScriptManager execution surface."""

from autonomous.script_manager import ScriptManager


def test_run_script_fails_closed():
    manager = ScriptManager()
    manager.registry["scripts"] = {
        "example": {
            "path": "scripts/example.py",
            "type": "python",
            "enabled": True,
        }
    }

    success, output = manager.run_script("example")

    assert success is False
    assert "FactoryAuthorityGateway" in output


def test_cron_mutation_fails_closed():
    manager = ScriptManager()
    assert manager.add_cron_job("example", "*/5 * * * *")[0] is False
    assert manager.remove_cron_job("example")[0] is False
