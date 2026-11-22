"""Evidence-backed financial balance reads.

Local finance snapshots are not authoritative unless a recent verification record
binds the amount to the same wallet and to successful on-chain token queries.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from finance.private_state import private_finance_hub_path

DEFAULT_MAX_AGE_SECONDS = 15 * 60
FINANCE_HUB = private_finance_hub_path()


def _parse_timestamp(value: Any):
    if not isinstance(value, str) or not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            return None
        return parsed.astimezone(timezone.utc)
    except ValueError:
        return None


def read_verified_polymarket_balance(
    hub_path: Path | str = FINANCE_HUB,
    *,
    now: datetime | None = None,
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
) -> dict:
    """Return a spendable balance only from a recent, complete Polygon RPC proof."""
    unknown = {
        "verified": False,
        "status": "unknown",
        "balance_usdc": None,
        "wallet_configured": False,
        "observed_at": None,
        "source": "private_finance_state",
        "reason": "No recent complete Polygon RPC verification record",
    }
    try:
        hub = json.loads(Path(hub_path).read_text(encoding="utf-8"))
        accounts = hub.get("accounts", {})
        if not isinstance(accounts, dict):
            return {**unknown, "reason": "Finance account data is malformed"}
        account = accounts.get("polymarket", {})
        if not isinstance(account, dict):
            return {**unknown, "reason": "Polymarket account data is malformed"}
        proof = account.get("balance_verification", {})
        if not isinstance(proof, dict):
            return {**unknown, "reason": "Balance verification proof is malformed"}
    except (OSError, ValueError, TypeError, AttributeError):
        return {**unknown, "reason": "Finance hub unavailable or malformed"}

    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parent.parent / ".env.polymarket", override=False)
    except ImportError:
        pass
    wallet = os.getenv("POLYMARKET_FUNDER_ADDRESS")
    if not isinstance(wallet, str) or re.fullmatch(r"0x[0-9a-fA-F]{40}", wallet) is None:
        return {**unknown, "reason": "Private wallet configuration is missing or invalid"}

    if proof.get("status") != "verified" or proof.get("source") != "polygon_rpc":
        return {**unknown, "wallet_configured": True, "reason": "Balance proof is not verified"}

    fingerprint = hashlib.sha256(wallet.lower().encode("ascii")).hexdigest()
    if (
        proof.get("chain") != "polygon"
        or proof.get("chain_id") != 137
        or proof.get("wallet_fingerprint") != fingerprint
    ):
        return {**unknown, "wallet_configured": True, "reason": "Proof wallet or chain does not match"}

    observed = _parse_timestamp(proof.get("observed_at"))
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if observed is None:
        return {**unknown, "wallet_configured": True, "reason": "Verification timestamp is invalid"}
    age = (current - observed).total_seconds()
    if age < 0 or age > max_age_seconds:
        return {
            **unknown,
            "wallet_configured": True,
            "observed_at": proof.get("observed_at"),
            "reason": "Verification record is stale or from the future",
        }

    tokens = proof.get("tokens", {})
    if not isinstance(tokens, dict):
        return {**unknown, "wallet_configured": True, "reason": "Token verification data is malformed"}
    values = []
    for token_name in ("usdc_bridged", "usdc_native"):
        token = tokens.get(token_name, {})
        value = token.get("balance")
        if token.get("status") != "verified" or isinstance(value, bool):
            return {**unknown, "wallet_configured": True, "observed_at": proof.get("observed_at"),
                    "reason": f"{token_name} balance is not verified"}
        try:
            value = float(value)
        except (TypeError, ValueError):
            return {**unknown, "wallet_configured": True, "observed_at": proof.get("observed_at"),
                    "reason": f"{token_name} balance is invalid"}
        if not math.isfinite(value) or value < 0:
            return {**unknown, "wallet_configured": True, "observed_at": proof.get("observed_at"),
                    "reason": f"{token_name} balance is invalid"}
        values.append(value)

    return {
        "verified": True,
        "status": "verified",
        "balance_usdc": sum(values),
        "wallet_configured": True,
        "observed_at": proof["observed_at"],
        "source": "polygon_rpc",
        "age_seconds": age,
    }
