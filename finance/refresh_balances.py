#!/usr/bin/env python3
"""Refresh Polymarket wallet balances with complete Polygon RPC evidence."""

from __future__ import annotations

import hashlib
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests

from finance.hub_store import update_account

FINANCE_HUB = Path(__file__).resolve().parent.parent / "state" / "private_finance_hub.json"
POLYGON_RPC = "https://polygon-rpc.com"
POLYGON_CHAIN_ID = 137
USDC_BRIDGED = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
USDC_NATIVE = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"


def _valid_address(value: str) -> bool:
    return isinstance(value, str) and re.fullmatch(r"0x[0-9a-fA-F]{40}", value) is not None


def _rpc_call(method: str, params: list) -> dict | None:
    try:
        response = requests.post(
            POLYGON_RPC,
            json={"jsonrpc": "2.0", "method": method, "params": params, "id": 1},
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or payload.get("error") is not None:
            return None
        return payload
    except (requests.RequestException, ValueError, TypeError):
        return None


def get_chain_id() -> int | None:
    payload = _rpc_call("eth_chainId", [])
    raw = payload.get("result") if payload else None
    try:
        return int(raw, 16) if isinstance(raw, str) and raw.startswith("0x") else None
    except ValueError:
        return None


def get_erc20_balance(wallet: str, contract: str, decimals: int = 6) -> float | None:
    """Fetch ERC20 balance; RPC errors and malformed responses remain unknown."""
    if not _valid_address(wallet) or not _valid_address(contract):
        return None
    data = f"0x70a08231000000000000000000000000{wallet[2:].lower()}"
    payload = _rpc_call("eth_call", [{"to": contract, "data": data}, "latest"])
    raw = payload.get("result") if payload else None
    if not isinstance(raw, str) or re.fullmatch(r"0x[0-9a-fA-F]+", raw) is None:
        return None
    try:
        value = int(raw, 16) / (10 ** decimals)
        return value if math.isfinite(value) and value >= 0 else None
    except (ValueError, OverflowError):
        return None


def get_native_balance(wallet: str, decimals: int = 18) -> float | None:
    """Fetch native POL balance; errors remain unknown."""
    if not _valid_address(wallet):
        return None
    payload = _rpc_call("eth_getBalance", [wallet, "latest"])
    raw = payload.get("result") if payload else None
    if not isinstance(raw, str) or re.fullmatch(r"0x[0-9a-fA-F]+", raw) is None:
        return None
    try:
        value = int(raw, 16) / (10 ** decimals)
        return value if math.isfinite(value) and value >= 0 else None
    except (ValueError, OverflowError):
        return None


def refresh() -> dict:
    """Update only from complete on-chain evidence; never infer from stale values."""
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).resolve().parent.parent / ".env.polymarket", override=False)
    except ImportError:
        pass
    wallet = os.getenv("POLYMARKET_FUNDER_ADDRESS")
    if not _valid_address(wallet):
        raise ValueError("POLYMARKET_FUNDER_ADDRESS is missing or invalid")
    observed_at = datetime.now(timezone.utc).isoformat()
    wallet_fingerprint = hashlib.sha256(wallet.lower().encode("ascii")).hexdigest()

    chain_id = get_chain_id()
    if chain_id == POLYGON_CHAIN_ID:
        bridged = get_erc20_balance(wallet, USDC_BRIDGED)
        native = get_erc20_balance(wallet, USDC_NATIVE)
        gas = get_native_balance(wallet)
    else:
        bridged = native = gas = None
    complete = chain_id == POLYGON_CHAIN_ID and bridged is not None and native is not None

    proof = {
        "status": "verified" if complete else "partial",
        "source": "polygon_rpc",
        "chain": "polygon",
        "chain_id": chain_id,
        "wallet_fingerprint": wallet_fingerprint,
        "observed_at": observed_at,
        "tokens": {
            "usdc_bridged": {
                "contract": USDC_BRIDGED,
                "balance": bridged,
                "status": "verified" if bridged is not None else "unknown",
            },
            "usdc_native": {
                "contract": USDC_NATIVE,
                "balance": native,
                "status": "verified" if native is not None else "unknown",
            },
        },
    }
    account_updates = {
        "balance_verification": proof,
        "balance_status": proof["status"],
    }
    if complete:
        account_updates["balance_usdc"] = bridged + native
        account_updates["last_updated"] = observed_at
    if gas is not None:
        account_updates["balance_matic"] = gas
        account_updates["gas_last_updated"] = observed_at

    update_account(
        FINANCE_HUB,
        "polymarket",
        account_updates,
        remove_keys=("wallet_address",),
        top_level_updates={"last_updated": observed_at},
    )

    result = {
        "status": proof["status"],
        "verified": complete,
        "wallet_configured": True,
        "observed_at": observed_at,
        "balance_usdc": bridged + native if complete else None,
        "balance_matic": gas,
    }
    print("Polymarket balance refresh:", "VERIFIED" if complete else "PARTIAL / UNKNOWN")
    return result


if __name__ == "__main__":
    refresh()
