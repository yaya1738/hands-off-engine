import unittest
from unittest import mock

from scripts.factory_execution_adapter import execute_factory_command


class FactoryExecutionAdapterTests(unittest.TestCase):
    def test_live_requires_approval(self):
        result = execute_factory_command(
            {"id": "fx-1", "mode": "LIVE", "objective": "inspect runtime"},
            execution_gate=True,
        )
        self.assertEqual(result["status"], "approval_required")

    def test_approved_live_still_requires_executor_gate(self):
        result = execute_factory_command(
            {"id": "fx-2", "mode": "LIVE", "approval_status": "approved", "objective": "inspect runtime"},
            execution_gate=False,
        )
        self.assertEqual(result["status"], "awaiting_executor_gate")

    def test_dryrun_remains_non_executing(self):
        result = execute_factory_command(
            {"id": "fx-3", "mode": "DRYRUN", "objective": "inspect runtime"},
            execution_gate=False,
        )
        self.assertEqual(result["status"], "dryrun_only")

    def test_missing_objective_fails_closed(self):
        result = execute_factory_command(
            {"id": "fx-4", "mode": "LIVE", "approval_status": "approved"},
            execution_gate=True,
        )
        self.assertEqual(result["status"], "rejected")

    def test_approved_command_is_blocked_by_queue_only_gateway(self):
        result = execute_factory_command(
            {
                "id": "fx-5",
                "mode": "LIVE",
                "approval_status": "approved",
                "objective": "inspect runtime",
                "reply_to": "mailbox-42",
            },
            execution_gate=True,
        )
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["command_id"], "fx-5")
        self.assertEqual(result["correlation_id"], "mailbox-42")
        self.assertFalse(result["execution_enabled"])
        self.assertIn("queue-only", result["reason"])

    def test_action_name_cannot_substitute_for_objective(self):
        result = execute_factory_command(
            {
                "id": "fx-6",
                "mode": "LIVE",
                "approval_status": "approved",
                "payload": {"action": "factory_execute"},
            },
            execution_gate=True,
        )
        self.assertEqual(result["status"], "rejected")

    def test_listener_routes_factory_command_through_adapter(self):
        import scripts.system_listener_inline as listener
        calls = {}

        def fake_execute(command, execution_gate=False):
            calls["command"] = command
            calls["execution_gate"] = execution_gate
            return {
                "status": "blocked",
                "command_id": command["id"],
                "correlation_id": command["correlation_id"],
                "execution_enabled": False,
            }

        with mock.patch.object(listener, "execute_factory_command", fake_execute):
            result = listener.process_command({
                "id": "fx-listener-1",
                "action": "execute",
                "target": "factory",
                "mode": "LIVE",
                "approval_status": "approved",
                "objective": "inspect runtime",
                "reply_to": "mailbox-77",
                "payload": {"objective": "inspect runtime"},
            })
        self.assertEqual(result["command_status"], "blocked")
        self.assertEqual(result["execution_result"]["correlation_id"], "mailbox-77")
        self.assertTrue(calls["execution_gate"])
        self.assertEqual(calls["command"]["objective"], "inspect runtime")

    def test_listener_rejects_factory_command_without_objective(self):
        import scripts.system_listener_inline as listener
        calls = []

        def fake_execute(command, execution_gate=False):
            calls.append(command)
            return {"status": "completed"}

        with mock.patch.object(listener, "execute_factory_command", fake_execute):
            result = listener.process_command({
                "id": "fx-listener-missing-objective",
                "action": "execute",
                "target": "factory",
                "mode": "LIVE",
                "approval_status": "approved",
                "payload": {"action": "factory_execute"},
            })
        self.assertEqual(result["command_status"], "rejected")
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
