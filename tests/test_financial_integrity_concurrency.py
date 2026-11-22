"""Regression coverage for fail-closed balance monitoring and ledger concurrency."""

import json
from concurrent.futures import ThreadPoolExecutor

from audit.ledger import FinancialLedger
from scripts import payment_monitor


def test_payment_monitor_does_not_promote_partial_rpc_data(tmp_path, monkeypatch):
    state_path = tmp_path / "payment-monitor.json"
    original = {
        "last_balance": 41.25,
        "last_check": "2026-01-01T00:00:00+00:00",
        "payments": [{"amount": 12.0}],
    }
    state_path.write_text(json.dumps(original), encoding="utf-8")
    monkeypatch.setattr(payment_monitor, "STATE_FILE", state_path)
    values = iter([41.25, None])
    monkeypatch.setattr(payment_monitor, "get_token_balance", lambda *_: next(values))

    result = payment_monitor.main()

    assert result == {"status": "unknown", "balance_usdc": None}
    assert json.loads(state_path.read_text(encoding="utf-8")) == original


def test_payment_monitor_rpc_error_is_unknown_not_zero(monkeypatch):
    class Response:
        def raise_for_status(self):
            return None

        def json(self):
            return {"jsonrpc": "2.0", "error": {"code": -32000, "message": "unavailable"}}

    monkeypatch.setattr(payment_monitor.requests, "post", lambda *args, **kwargs: Response())
    assert payment_monitor.get_token_balance(payment_monitor.WALLET, payment_monitor.USDC_CONTRACT) is None


def test_ledger_concurrent_appends_preserve_hash_chain(tmp_path):
    ledger_path = tmp_path / "ledger.jsonl"
    ledger = FinancialLedger(str(ledger_path))

    def append(index):
        return ledger.add_cost(
            component="concurrency-test",
            action=f"append-{index}",
            amount=1.0,
            session_id="test",
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        entries = list(pool.map(append, range(32)))

    assert len(entries) == 32
    assert ledger.verify_integrity() is True
    rows = [json.loads(line) for line in ledger_path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 33
    assert len({row["entry_id"] for row in rows}) == 33
    for previous, current in zip(rows, rows[1:]):
        assert current["previous_hash"] == previous["current_hash"]


def test_ledger_idempotency_is_checked_inside_append_lock(tmp_path):
    ledger = FinancialLedger(str(tmp_path / "ledger.jsonl"))
    evidence = {
        "verification": {
            "status": "verified",
            "source_type": "bank_transaction",
            "evidence_ref": "statement-row-123",
            "idempotency_key": "bank:statement-row-123",
            "verified_by": "test",
            "verified_at": "2026-11-22T00:00:00+00:00",
        }
    }
    ledger.add_revenue("test", "settlement", 5.0, "session", evidence)
    try:
        ledger.add_revenue("test", "settlement", 5.0, "session", evidence)
    except ValueError as exc:
        assert "Duplicate financial evidence" in str(exc)
    else:
        raise AssertionError("duplicate evidence must be rejected")
    assert len(ledger.get_entries()) == 1
    assert ledger.verify_integrity() is True
