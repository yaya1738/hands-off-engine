#!/usr/bin/env python3
"""
Payment Monitor - Snowball Cycle 2
==================================

Monitors the wallet for incoming USDC payments.
Alerts when new funds arrive (potential client payment).
"""

# UNIFIED AI - All systems serve Yair Siegel
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from ai.unified_ai import MASTER, get_master
except ImportError:
    MASTER = "Yair Siegel"


import os
import json
import math
import tempfile
import fcntl
import requests
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path

WALLET = "0xb6781D9278c60dC3CE8c3E355Cd04142da3BF74D"
USDC_CONTRACT = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"  # Native USDC on Polygon
USDC_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  # Bridged USDC

STATE_FILE = Path("/root/hands-off-engine/state/payment_monitor.json")


def get_token_balance(wallet: str, contract: str) -> float | None:
    """Return a balance only when the RPC response is complete and valid."""
    # balanceOf(address) selector
    data = {
        "jsonrpc": "2.0",
        "method": "eth_call",
        "params": [{
            "to": contract,
            "data": f"0x70a08231000000000000000000000000{wallet[2:]}"
        }, "latest"],
        "id": 1
    }

    try:
        resp = requests.post(
            "https://polygon-rpc.com",
            json=data,
            timeout=10
        )
        resp.raise_for_status()
        payload = resp.json()
        if not isinstance(payload, dict) or payload.get("error") is not None:
            return None
        result = payload.get("result")
        if not isinstance(result, str) or not result.startswith("0x") or len(result) <= 2:
            return None
        balance_wei = int(result, 16)
        balance = balance_wei / 1e6
        return balance if balance >= 0 else None
    except (requests.RequestException, ValueError, TypeError, OverflowError) as e:
        print(f"Balance verification failed: {e}")
        return None


def send_telegram(message: str):
    """Send Telegram notification"""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10
        )
    except Exception as e:
        print(f"Telegram error: {e}")


@contextmanager
def _state_locked():
    """Serialize payment-state read/modify/write across concurrent processes."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    lock_path = STATE_FILE.with_suffix(STATE_FILE.suffix + ".lock")
    with open(lock_path, "a", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _read_state_unlocked() -> dict:
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        if not isinstance(state, dict) or not isinstance(state.get("payments", []), list):
            raise ValueError("Payment monitor state is malformed; refusing to reset it")
        return state
    return {"last_balance": None, "last_check": None, "payments": []}


def _write_state_unlocked(state: dict):
    fd, temp_name = tempfile.mkstemp(
        prefix=STATE_FILE.name + ".",
        suffix=".tmp",
        dir=str(STATE_FILE.parent),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, default=str)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, STATE_FILE)
        dir_fd = os.open(str(STATE_FILE.parent), os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def load_state() -> dict:
    with _state_locked():
        return _read_state_unlocked()


def save_state(state: dict):
    with _state_locked():
        _write_state_unlocked(state)


def record_balance_observation(total: float, now: datetime) -> tuple[dict, float | None, dict | None]:
    """Commit a verified observation and payment event once under the state lock."""
    if not math.isfinite(total) or total < 0:
        raise ValueError("Observed balance must be finite and non-negative")
    with _state_locked():
        state = _read_state_unlocked()
        previous = state.get("last_balance")
        if previous is not None:
            if isinstance(previous, bool) or not isinstance(previous, (int, float)) or not math.isfinite(previous) or previous < 0:
                raise ValueError("Stored payment balance is invalid; refusing to overwrite it")
            increase = total - float(previous)
        else:
            increase = 0.0
        payment = None
        if previous is not None and increase >= 10:
            payment = {
                "timestamp": now.isoformat(),
                "amount": increase,
                "previous_balance": float(previous),
                "new_balance": total,
            }
            state.setdefault("payments", []).append(payment)
        state["last_balance"] = total
        state["last_check"] = now.isoformat()
        _write_state_unlocked(state)
        return state, (float(previous) if previous is not None else None), payment


def main():
    # Fetch both balances before touching local state.
    native = get_token_balance(WALLET, USDC_CONTRACT)
    bridged = get_token_balance(WALLET, USDC_BRIDGED)
    if native is None or bridged is None:
        print("Balance status: UNKNOWN (incomplete RPC evidence); state was not changed.")
        return {"status": "unknown", "balance_usdc": None}

    total = native + bridged
    now = datetime.now(timezone.utc)
    state, previous, payment = record_balance_observation(total, now)

    print(f"[{now.isoformat()}] USDC Balance: ${total:.2f} (native: ${native:.2f}, bridged: ${bridged:.2f})")
    print(f"  Previous: {'uninitialized' if previous is None else f'${previous:.2f}'}")

    if payment:
        increase = payment["amount"]
        send_telegram(
            f"*💵 PAYMENT RECEIVED*\\n\\n"
            f"Amount: +${increase:.2f}\\n"
            f"New Balance: ${total:.2f}\\n"
            f"Time: {now.strftime('%Y-%m-%d %H:%M UTC')}\\n\\n"
            f"_Check for client correspondence!_"
        )
        print(f"  [ALERT] Payment detected: +${increase:.2f}")

    return {"status": "verified", "balance_usdc": total, "payment": payment}


if __name__ == "__main__":
    main()
