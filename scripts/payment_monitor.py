#!/usr/bin/env python3
"""Observe verified Polygon USDC balance changes and alert on material increases.

This monitor is read-only with respect to financial accounts. It never sends,
signs, or submits transactions. A first observation establishes a baseline and
is not classified as income.
"""

from __future__ import annotations

import fcntl
import json
import math
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from finance.refresh_balances import (
    POLYGON_CHAIN_ID,
    USDC_BRIDGED,
    USDC_NATIVE,
    get_chain_id,
    get_erc20_balance,
)

BASE_DIR = Path(__file__).resolve().parent.parent
STATE_FILE = BASE_DIR / "state" / "payment_monitor.json"


def _load_wallet_configuration() -> str | None:
    """Load the local wallet address without embedding it in public source."""
    try:
        from dotenv import load_dotenv
        load_dotenv(BASE_DIR / ".env.polymarket", override=False)
    except ImportError:
        pass
    wallet = os.getenv("POLYMARKET_FUNDER_ADDRESS")
    if not isinstance(wallet, str) or len(wallet) != 42 or not wallet.startswith("0x"):
        return None
    if any(char not in "0123456789abcdefABCDEF" for char in wallet[2:]):
        return None
    return wallet


def get_verified_balance(wallet: str) -> tuple[float, float, float] | None:
    """Require Polygon mainnet and complete reads of both supported USDC tokens."""
    if get_chain_id() != POLYGON_CHAIN_ID:
        return None
    native = get_erc20_balance(wallet, USDC_NATIVE)
    bridged = get_erc20_balance(wallet, USDC_BRIDGED)
    if native is None or bridged is None:
        return None
    total = native + bridged
    if not math.isfinite(total) or total < 0:
        return None
    return total, native, bridged


def send_telegram(message: str) -> bool:
    """Send an alert only when notification credentials are configured."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        return False
    try:
        import requests
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"},
            timeout=10,
        )
        response.raise_for_status()
        return True
    except Exception as exc:
        print(f"Telegram error: {exc}")
        return False


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
        if (
            not isinstance(state, dict)
            or not isinstance(state.get("payments", []), list)
        ):
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
            json.dump(state, handle, indent=2)
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


def record_balance_observation(
    total: float, now: datetime
) -> tuple[dict, float | None, dict | None]:
    """Commit a verified observation and payment event once under the state lock."""
    if (
        isinstance(total, bool)
        or not isinstance(total, (int, float))
        or not math.isfinite(total)
        or total < 0
    ):
        raise ValueError("Observed balance must be finite and non-negative")
    with _state_locked():
        state = _read_state_unlocked()
        previous = state.get("last_balance")
        if previous is not None:
            if (
                isinstance(previous, bool)
                or not isinstance(previous, (int, float))
                or not math.isfinite(previous)
                or previous < 0
            ):
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
        state["last_balance"] = float(total)
        state["last_check"] = now.isoformat()
        _write_state_unlocked(state)
        return state, (float(previous) if previous is not None else None), payment


def main():
    wallet = _load_wallet_configuration()
    if wallet is None:
        print("Balance status: UNKNOWN (private wallet configuration missing or invalid).")
        return {"status": "unknown", "balance_usdc": None}

    observation = get_verified_balance(wallet)
    if observation is None:
        print("Balance status: UNKNOWN (incomplete Polygon RPC evidence); state was not changed.")
        return {"status": "unknown", "balance_usdc": None}

    total, native, bridged = observation
    now = datetime.now(timezone.utc)
    state, previous, payment = record_balance_observation(total, now)

    print(
        f"[{now.isoformat()}] USDC Balance: ${total:.2f} "
        f"(native: ${native:.2f}, bridged: ${bridged:.2f})"
    )
    previous_text = "uninitialized" if previous is None else f"${previous:.2f}"
    print(f"  Previous: {previous_text}")

    if payment:
        send_telegram(
            "*💵 PAYMENT RECEIVED*\n\n"
            f"Amount: +${payment['amount']:.2f}\n"
            f"New Balance: ${total:.2f}\n"
            f"Time: {now.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
            "_Check for client correspondence!_"
        )
        print(f"  [ALERT] Balance increase observed: +${payment['amount']:.2f}")

    return {"status": "verified", "balance_usdc": total, "payment": payment}


if __name__ == "__main__":
    main()
