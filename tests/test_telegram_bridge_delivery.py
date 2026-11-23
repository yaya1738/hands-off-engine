"""Telegram delivery status must reflect every API response, including chunks."""
import unittest
from unittest import mock

from scripts import telegram_bridge


def make_bridge():
    bridge = telegram_bridge.TelegramBridge.__new__(telegram_bridge.TelegramBridge)
    bridge.config = {"token": "test", "chat_ids": [123]}
    bridge.state = {"messages_sent": 0}
    bridge.available = True
    return bridge


class TelegramBridgeDeliveryTests(unittest.TestCase):
    def test_api_rejection_is_reported_as_failed_and_not_counted(self):
        bridge = make_bridge()
        with mock.patch.object(bridge, "_api_call", return_value={"ok": False, "description": "blocked"}), \
             mock.patch.object(telegram_bridge, "save_state"):
            result = bridge.send("hello")

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["sent_chunks"], 0)
        self.assertEqual(result["failed_chunks"], 1)
        self.assertEqual(result["errors"], [{"chunk": 1, "error": "blocked"}])
        self.assertEqual(bridge.state["messages_sent"], 0)

    def test_transport_failure_is_reported_as_failed_and_not_counted(self):
        bridge = make_bridge()
        with mock.patch.object(telegram_bridge.urllib.request, "urlopen", side_effect=OSError("connection reset")), \
             mock.patch.object(telegram_bridge, "save_state"):
            result = bridge.send("hello")

        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["sent_chunks"], 0)
        self.assertEqual(bridge.state["messages_sent"], 0)
        self.assertIn("connection reset", result["errors"][0]["error"])

    def test_partial_multi_chunk_delivery_is_reported_truthfully(self):
        bridge = make_bridge()
        text = "x" * (telegram_bridge.MAX_MESSAGE_LENGTH + 10)
        with mock.patch.object(
            bridge, "_api_call",
            side_effect=[{"ok": True}, {"ok": False, "description": "second chunk rejected"}],
        ), mock.patch.object(telegram_bridge, "save_state"):
            result = bridge.send(text)

        self.assertEqual(result["status"], "partial_failure")
        self.assertEqual(result["chunks"], 2)
        self.assertEqual(result["sent_chunks"], 1)
        self.assertEqual(result["failed_chunks"], 1)
        self.assertEqual(bridge.state["messages_sent"], 1)
        self.assertEqual(result["errors"], [{"chunk": 2, "error": "second chunk rejected"}])

    def test_all_chunks_must_confirm_ok_before_status_is_sent(self):
        bridge = make_bridge()
        text = "x" * (telegram_bridge.MAX_MESSAGE_LENGTH + 10)
        with mock.patch.object(bridge, "_api_call", return_value={"ok": True}), \
             mock.patch.object(telegram_bridge, "save_state"):
            result = bridge.send(text)

        self.assertEqual(result["status"], "sent")
        self.assertEqual(result["sent_chunks"], 2)
        self.assertEqual(result["failed_chunks"], 0)
        self.assertEqual(bridge.state["messages_sent"], 2)

    def test_empty_message_is_not_reported_as_sent(self):
        bridge = make_bridge()
        with mock.patch.object(bridge, "_api_call") as api, mock.patch.object(telegram_bridge, "save_state"):
            result = bridge.send("")

        self.assertEqual(result["status"], "failed")
        api.assert_not_called()


if __name__ == "__main__":
    unittest.main()
