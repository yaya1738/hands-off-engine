"""Telegram delivery must only be reported when Telegram confirms each chunk."""
import unittest
from unittest import mock

from scripts import telegram_bridge


class TelegramBridgeDeliveryTests(unittest.TestCase):
    def setUp(self):
        self.config = {"token": "test-token", "chat_ids": [12345]}
        self.patches = [
            mock.patch.object(telegram_bridge, "load_config", return_value=self.config),
            mock.patch.object(
                telegram_bridge,
                "load_state",
                return_value={"last_update_id": 0, "messages_sent": 0, "messages_received": 0},
            ),
            mock.patch.object(telegram_bridge, "save_state"),
        ]
        for patcher in self.patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.bridge = telegram_bridge.TelegramBridge()

    def test_api_rejection_is_not_reported_as_sent(self):
        with mock.patch.object(
            self.bridge, "_api_call",
            return_value={"ok": False, "description": "chat not found"},
        ):
            result = self.bridge.send("hello")

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["sent_chunks"], 0)
        self.assertEqual(result["failed_chunks"], 1)
        self.assertEqual(self.bridge.state["messages_sent"], 0)

    def test_transport_failure_is_not_reported_as_sent(self):
        with mock.patch.object(
            self.bridge, "_api_call",
            return_value={"ok": False, "error": "timed out"},
        ):
            result = self.bridge.send("hello")

        self.assertEqual(result["status"], "error")
        self.assertEqual(self.bridge.state["messages_sent"], 0)

    def test_partial_multichunk_failure_reports_only_confirmed_delivery(self):
        responses = [
            {"ok": True, "result": {"message_id": 1}},
            {"ok": False, "error": "connection reset"},
        ]
        with mock.patch.object(self.bridge, "_api_call", side_effect=responses):
            result = self.bridge.send("x" * (telegram_bridge.MAX_MESSAGE_LENGTH + 1))

        self.assertEqual(result["status"], "partial_failure")
        self.assertEqual(result["chunks"], 2)
        self.assertEqual(result["sent_chunks"], 1)
        self.assertEqual(result["failed_chunks"], 1)
        self.assertEqual(self.bridge.state["messages_sent"], 1)

    def test_all_chunks_must_be_confirmed_before_sent_status(self):
        with mock.patch.object(
            self.bridge, "_api_call",
            return_value={"ok": True, "result": {"message_id": 1}},
        ):
            result = self.bridge.send("hello")

        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["sent_chunks"], 1)
        self.assertEqual(result["failed_chunks"], 0)
        self.assertEqual(self.bridge.state["messages_sent"], 1)


if __name__ == "__main__":
    unittest.main()
