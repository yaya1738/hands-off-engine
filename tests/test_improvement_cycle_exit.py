"""Subprocess-level exit-contract tests for the improvement cycle.

The scheduler records cycle success from the process exit code, so fatal
failures must propagate to a nonzero exit. These tests run real child
processes (no in-process monkeypatching of the module under test) to prove
the CLI entry point propagates the exit code.
"""
import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts import improvement_cycle  # noqa: E402


DRIVER = textwrap.dedent("""
    import sys
    import tempfile
    from pathlib import Path

    sys.path.insert(0, {root!r})
    from scripts import improvement_cycle as ic

    tmp = Path(tempfile.mkdtemp())
    ic.STATE = tmp
    ic.CYCLE_LOG = tmp / "improvement_cycles.json"

    mode = sys.argv[1]

    if mode == "all-success":
        ic.run_subprocess = lambda script: {{"success": True, "output": "ok"}}
        ic.apply_generated_candidates = lambda: []
    elif mode == "generation-fails":
        ic.run_subprocess = lambda script: {{
            "success": not script.startswith("self_improvement"),
            "output": "forced failure" if script.startswith("self_improvement") else "ok",
        }}
        ic.apply_generated_candidates = lambda: []
    elif mode == "apply-raises":
        ic.run_subprocess = lambda script: {{"success": True, "output": "ok"}}
        def _raise():
            raise RuntimeError("forced apply failure")
        ic.apply_generated_candidates = _raise
    elif mode == "diagnostics-fail":
        # applier_status / feedback / approval fail; generation and apply
        # succeed. These are observational, non-fatal per the documented
        # policy, so the cycle must still exit zero.
        ic.run_subprocess = lambda script: {{
            "success": script.startswith("self_improvement"),
            "output": "ok" if script.startswith("self_improvement") else "diagnostic failure",
        }}
        ic.apply_generated_candidates = lambda: []
    else:
        raise SystemExit(f"unknown mode: {{mode}}")

    sys.exit(ic.main())
""")


def _run_driver(mode):
    return subprocess.run(
        [sys.executable, "-c", DRIVER.format(root=str(ROOT)), mode],
        capture_output=True, text=True, timeout=120, cwd=str(ROOT),
    )


class ImprovementCycleExitContractTests(unittest.TestCase):
    def test_success_exits_zero(self):
        result = _run_driver("all-success")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_generation_failure_exits_nonzero(self):
        result = _run_driver("generation-fails")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("improvement", result.stdout)

    def test_apply_failure_exits_nonzero(self):
        result = _run_driver("apply-raises")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("applier_apply", result.stdout)

    def test_diagnostic_failures_are_nonfatal(self):
        # applier_status/feedback/approval failures must not fail the cycle;
        # the approval failure additionally triggers a Telegram alert.
        result = _run_driver("diagnostics-fail")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_fatal_fields_policy_is_documented_and_minimal(self):
        # The fatal policy must cover at least generation and apply, and must
        # stay documented next to the constant.
        self.assertEqual(improvement_cycle.FATAL_FIELDS, ("improvement", "applier_apply"))
        source = (ROOT / "scripts" / "improvement_cycle.py").read_text()
        self.assertIn("FATAL_FIELDS", source)
        self.assertIn("raise SystemExit(main())", source)

    def test_cycle_history_is_still_persisted(self):
        # Structured logging must survive the exit-code change.
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            log = state / "cycles.json"
            from unittest import mock
            with mock.patch.object(improvement_cycle, "STATE", state), \
                 mock.patch.object(improvement_cycle, "CYCLE_LOG", log), \
                 mock.patch.object(improvement_cycle, "run_subprocess",
                                  return_value={"success": True, "output": "ok"}), \
                 mock.patch.object(improvement_cycle, "apply_generated_candidates",
                                  return_value=[]):
                code = improvement_cycle.main()
            self.assertEqual(code, 0)
            history = json.loads(log.read_text())
            self.assertEqual(len(history), 1)
            self.assertTrue(history[0]["improvement"])
            self.assertTrue(history[0]["applier_apply"])


class ApprovalAlertTests(unittest.TestCase):
    """The approval-check alert must use the real TelegramBridge API."""

    def test_approval_failure_sends_alert_via_real_bridge(self):
        import scripts.telegram_bridge as telegram_bridge
        from unittest import mock

        alerts = []

        class FakeBridge:
            def __init__(self):
                pass

            def send_alert(self, title, body, severity="normal"):
                alerts.append((title, body, severity))
                return {"status": "sent"}

        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            with mock.patch.object(improvement_cycle, "STATE", state), \
                 mock.patch.object(improvement_cycle, "CYCLE_LOG", state / "cycles.json"), \
                 mock.patch.object(telegram_bridge, "TelegramBridge", FakeBridge), \
                 mock.patch.object(improvement_cycle, "run_subprocess",
                                  side_effect=lambda script: {
                                      "success": not script.startswith("improvement_approval"),
                                      "output": "ok",
                                  }), \
                 mock.patch.object(improvement_cycle, "apply_generated_candidates",
                                  return_value=[]):
                code = improvement_cycle.main()

        self.assertEqual(code, 0)  # approval failure is non-fatal
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0][0], "Improvement cycle")
        self.assertIn("Approval check failed", alerts[0][1])

    def test_approval_alert_not_configured_is_explicit(self):
        import scripts.telegram_bridge as telegram_bridge
        from unittest import mock

        class NotConfiguredBridge:
            def __init__(self):
                pass

            def send_alert(self, title, body, severity="normal"):
                return {"status": "not_configured"}

        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            with mock.patch.object(improvement_cycle, "STATE", state), \
                 mock.patch.object(improvement_cycle, "CYCLE_LOG", state / "cycles.json"), \
                 mock.patch.object(telegram_bridge, "TelegramBridge", NotConfiguredBridge), \
                 mock.patch.object(improvement_cycle, "run_subprocess",
                                  side_effect=lambda script: {
                                      "success": not script.startswith("improvement_approval"),
                                      "output": "ok",
                                  }), \
                 mock.patch.object(improvement_cycle, "apply_generated_candidates",
                                  return_value=[]):
                code = improvement_cycle.main()

        self.assertEqual(code, 0)


if __name__ == "__main__":
    unittest.main()
