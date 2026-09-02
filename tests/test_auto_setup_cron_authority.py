from pathlib import Path

SOURCE = Path("scripts/auto_setup_cron.py").read_text()


def test_cron_setup_has_no_process_execution_or_mutation():
    assert "import subprocess" not in SOURCE
    assert "subprocess." not in SOURCE
    assert "crontab" not in SOURCE.lower()


def test_install_and_remove_fail_closed():
    namespace = {"__name__": "auto_setup_cron_test"}
    exec(compile(SOURCE, "scripts/auto_setup_cron.py", "exec"), namespace)
    assert namespace["install_cron_jobs"]() is False
    assert namespace["remove_cron_jobs"]() is False
