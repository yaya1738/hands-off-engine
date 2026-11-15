"""Regression tests: redacted finance inputs must never become measured zeroes."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relative_path):
    path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cards_editor = load_module("cards_limits_fill", "termux-hands-off/agents/cards_limits_fill.py")
credit = load_module("credit_utilization", "termux-hands-off/agents/credit_utilization.py")
statement = load_module("statement_watchdog", "termux-hands-off/agents/statement_watchdog.py")


class FinanceRedactionSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.cards_path = Path(self.temp.name) / "cards.json"
        for module in (cards_editor, credit, statement):
            module.CARDS = self.cards_path

    def tearDown(self):
        self.temp.cleanup()

    def write_cards(self, payload):
        self.cards_path.write_text(json.dumps(payload), encoding="utf-8")

    def test_editor_refuses_to_invent_missing_card_data(self):
        with self.assertRaises(SystemExit):
            cards_editor.load_cards()

    def test_editor_preserves_explicit_unknown_values(self):
        payload = {"card_a": {"limit": None, "balance": None, "statement_day": None},
                   "_data_status": "redacted_unknown"}
        self.write_cards(payload)
        self.assertEqual(cards_editor.load_cards(), payload)

    def test_credit_utilization_reports_redacted_values_as_unknown(self):
        self.write_cards({"card_a": {"limit": None, "balance": None},
                          "_data_status": "redacted_unknown"})
        cards, reason = credit.load_cards()
        self.assertIsNone(cards)
        self.assertIn("unknown", reason)

    def test_statement_watchdog_reports_redacted_values_as_unknown(self):
        self.write_cards({"card_a": {"limit": None, "balance": None, "statement_day": None},
                          "_data_status": "redacted_unknown"})
        cards, reason = statement.load_cards()
        self.assertIsNone(cards)
        self.assertIn("unknown", reason)

    def test_measured_zero_balance_remains_a_valid_measurement(self):
        payload = {"card_a": {"limit": 1000, "balance": 0, "statement_day": 15}}
        self.write_cards(payload)
        credit_cards, credit_error = credit.load_cards()
        statement_cards, statement_error = statement.load_cards()
        self.assertIsNone(credit_error)
        self.assertIsNone(statement_error)
        self.assertEqual(credit_cards[0]["balance"], 0)
        self.assertEqual(statement_cards[0]["balance"], 0)

    def test_metadata_only_file_does_not_become_zero_utilization(self):
        self.write_cards({"_data_status": "redacted_unknown"})
        self.assertIsNone(credit.load_cards()[0])
        self.assertIsNone(statement.load_cards()[0])


if __name__ == "__main__":
    unittest.main()
