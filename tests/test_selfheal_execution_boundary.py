import infrastructure.selfheal as selfheal


def test_restart_service_ignores_configured_shell_commands(monkeypatch):
    controller = selfheal.SelfHealController.__new__(selfheal.SelfHealController)
    controller.config = {
        "restart_commands": {
            "orchestrator": "touch /tmp/selfheal-shell-injection",
        }
    }
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""
        return Result()

    monkeypatch.setattr(selfheal.subprocess, "run", fake_run)

    assert controller._restart_service("orchestrator") is True
    assert calls == [
        (["systemctl", "restart", "hands-off-orchestrator"], {
            "capture_output": True,
            "text": True,
            "timeout": 30,
            "check": False,
        })
    ]


def test_cleanup_patterns_are_data_not_shell_commands(monkeypatch):
    controller = selfheal.SelfHealController.__new__(selfheal.SelfHealController)
    controller.config = {
        "disk_cleanup": {
            "cleanup_patterns": [
                "/tmp/hands-off-*; touch /tmp/selfheal-shell-injection",
                "/etc/*",
            ],
            "max_backup_age_days": 30,
        }
    }

    def forbidden_run(*args, **kwargs):
        raise AssertionError("Self-heal cleanup must not invoke a shell")

    monkeypatch.setattr(selfheal.subprocess, "run", forbidden_run)
    monkeypatch.setattr(selfheal.glob, "glob", lambda pattern: [])

    assert controller._cleanup_old_files() is False


def test_stale_lock_detection_and_cleanup_do_not_use_shell(monkeypatch):
    controller = selfheal.SelfHealController.__new__(selfheal.SelfHealController)

    def forbidden_run(*args, **kwargs):
        raise AssertionError("Lock management must not invoke a shell")

    monkeypatch.setattr(selfheal.subprocess, "run", forbidden_run)
    monkeypatch.setattr(selfheal.glob, "glob", lambda pattern: [])

    assert controller._has_stale_locks() is False
    assert controller._clear_locks() is False
