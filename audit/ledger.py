#!/usr/bin/env python3
"""
Immutable financial ledger for tracking costs and revenues
Blockchain-inspired append-only ledger
"""
import hashlib
import json
import os
import fcntl
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class LedgerEntry:
    """Single ledger entry with cryptographic hash for immutability"""
    entry_id: str
    timestamp: str
    session_id: str
    component: str
    action: str
    amount: float  # Positive for revenue, negative for costs
    category: str  # "cost" or "revenue"
    metadata: Dict[str, Any]
    previous_hash: str
    current_hash: str
    verified: bool = False
    source_type: str = "unverified"
    evidence_ref: Optional[str] = None
    idempotency_key: Optional[str] = None
    hash_version: int = 2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class FinancialLedger:
    """
    Immutable financial ledger for tracking all costs and revenues

    Features:
    - Blockchain-inspired hash chaining for immutability
    - Separate cost and revenue tracking
    - Session-based analysis
    - ROI calculation
    - Budget recommendations
    """

    def __init__(self, ledger_file: str = "audit/ledger.jsonl"):
        self.ledger_file = Path(ledger_file)
        self.ledger_file.parent.mkdir(parents=True, exist_ok=True)

        # Genesis creation is serialized with every append across processes.
        self._create_genesis_entry()

    @contextmanager
    def _locked(self):
        """Cross-process exclusive lock for ledger read/modify/append sequences."""
        lock_path = self.ledger_file.with_suffix(self.ledger_file.suffix + ".lock")
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with open(lock_path, "a", encoding="utf-8") as lock_handle:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)

    def _create_genesis_entry(self):
        """Create the first entry exactly once, under the ledger lock."""
        with self._locked():
            if self.ledger_file.exists() and self.ledger_file.stat().st_size:
                return
            genesis = LedgerEntry(
                entry_id="genesis",
                timestamp=datetime.now(timezone.utc).isoformat(),
                session_id="system",
                component="ledger.system",
                action="initialize",
                amount=0.0,
                category="system",
                metadata={"description": "Genesis block"},
                previous_hash="0" * 64,
                current_hash=self._compute_hash("genesis", "0" * 64, 0.0),
                verified=False,
                source_type="system",
                hash_version=1,
            )
            with open(self.ledger_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(genesis.to_dict()) + "\\n")
                f.flush()
                os.fsync(f.fileno())

    def _append_entry(self, entry: LedgerEntry) -> LedgerEntry:
        """Atomically assign chain position, enforce idempotency, and append."""
        with self._locked():
            lines = self.ledger_file.read_text(encoding="utf-8").splitlines() if self.ledger_file.exists() else []
            previous_hash = "0" * 64
            seen_keys = set()
            for index, line in enumerate(lines):
                if not line.strip():
                    continue
                item = json.loads(line)
                if item.get("previous_hash") != previous_hash:
                    raise ValueError(f"Cannot append to broken ledger chain at line {index + 1}")
                if item.get("hash_version", 1) >= 2:
                    expected_hash = self._compute_entry_hash(item)
                else:
                    expected_hash = self._compute_hash(
                        item["entry_id"], item["previous_hash"], item["amount"]
                    )
                if item.get("current_hash") != expected_hash:
                    raise ValueError(f"Cannot append to tampered ledger at line {index + 1}")
                previous_hash = item["current_hash"]
                key = item.get("idempotency_key")
                if key:
                    seen_keys.add(key)
            if entry.idempotency_key and entry.idempotency_key in seen_keys:
                raise ValueError("Duplicate financial evidence: idempotency key already recorded")
            entry.previous_hash = previous_hash
            entry.current_hash = self._compute_entry_hash(entry.to_dict())
            with open(self.ledger_file, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry.to_dict()) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
        return entry

    def _compute_hash(self, entry_id: str, previous_hash: str, amount: float) -> str:
        """Compute SHA-256 hash for entry"""
        data = f"{entry_id}{previous_hash}{amount}".encode()
        return hashlib.sha256(data).hexdigest()

    def _compute_entry_hash(self, entry_data: Dict[str, Any]) -> str:
        """Hash all immutable entry fields, not just amount and chain pointer."""
        payload = {key: value for key, value in entry_data.items() if key != "current_hash"}
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _idempotency_exists(self, key: Optional[str]) -> bool:
        if not key:
            return False
        return any(entry.idempotency_key == key for entry in self.get_entries())

    def _get_last_hash(self) -> str:
        """Get hash of the last entry in the ledger"""
        if not self.ledger_file.exists():
            return "0" * 64

        with open(self.ledger_file, "r") as f:
            lines = f.readlines()
            if not lines:
                return "0" * 64

            last_entry = json.loads(lines[-1])
            return last_entry["current_hash"]

    def add_cost(
        self,
        component: str,
        action: str,
        amount: float,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LedgerEntry:
        """Record an estimated or evidenced cost without implying verification."""
        import math
        import uuid

        value = float(amount)
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Cost amount must be finite and positive")
        data = metadata or {}
        verification = data.get("verification", {}) if isinstance(data, dict) else {}
        verified = (
            isinstance(verification, dict)
            and verification.get("status") == "verified"
            and bool(verification.get("source_type"))
            and bool(verification.get("evidence_ref"))
        )
        idempotency_key = verification.get("idempotency_key") if verified else None
        entry = LedgerEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            component=component,
            action=action,
            amount=-abs(value),
            category="cost",
            metadata=data,
            previous_hash="",
            current_hash="",
            verified=bool(verified),
            source_type=verification.get("source_type", "unverified") if verified else "unverified",
            evidence_ref=verification.get("evidence_ref") if verified else None,
            idempotency_key=idempotency_key,
            hash_version=2,
        )
        return self._append_entry(entry)

    def add_revenue(
        self,
        component: str,
        action: str,
        amount: float,
        session_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LedgerEntry:
        """Record revenue only with explicit source evidence and idempotency."""
        import math
        import uuid

        value = float(amount)
        if not math.isfinite(value) or value <= 0:
            raise ValueError("Revenue amount must be finite and positive")
        data = metadata or {}
        verification = data.get("verification", {}) if isinstance(data, dict) else {}
        required = ("source_type", "evidence_ref", "idempotency_key", "verified_by", "verified_at")
        allowed_sources = {
            "bank_transaction",
            "payment_processor_settlement",
            "onchain_settlement",
            "exchange_fill_settlement",
            "invoice_payment",
        }
        if (
            not isinstance(verification, dict)
            or verification.get("status") != "verified"
            or any(not isinstance(verification.get(key), str) or not verification[key].strip() for key in required)
            or verification.get("source_type") not in allowed_sources
        ):
            raise ValueError(
                "Unverified revenue blocked: provide a verified source_type, evidence_ref and idempotency_key"
            )
        entry = LedgerEntry(
            entry_id=str(uuid.uuid4()),
            timestamp=datetime.now(timezone.utc).isoformat(),
            session_id=session_id,
            component=component,
            action=action,
            amount=abs(value),
            category="revenue",
            metadata=data,
            previous_hash="",
            current_hash="",
            verified=True,
            source_type=verification["source_type"],
            evidence_ref=verification["evidence_ref"],
            idempotency_key=verification["idempotency_key"],
            hash_version=2,
        )
        return self._append_entry(entry)

    def get_entries(
        self,
        session_id: Optional[str] = None,
        component: Optional[str] = None,
        category: Optional[str] = None
    ) -> List[LedgerEntry]:
        """
        Query ledger entries

        Args:
            session_id: Filter by session
            component: Filter by component
            category: Filter by category ("cost" or "revenue")

        Returns:
            List of matching LedgerEntry objects
        """
        if not self.ledger_file.exists():
            return []

        entries = []
        with open(self.ledger_file, "r") as f:
            for line in f:
                entry_data = json.loads(line.strip())

                # Skip genesis entry
                if entry_data["entry_id"] == "genesis":
                    continue

                # Apply filters
                if session_id and entry_data["session_id"] != session_id:
                    continue
                if component and entry_data["component"] != component:
                    continue
                if category and entry_data["category"] != category:
                    continue

                entries.append(LedgerEntry(**entry_data))

        return entries

    def verify_integrity(self) -> bool:
        """
        Verify ledger integrity by checking hash chain

        Returns:
            True if ledger is intact, False if tampered
        """
        if not self.ledger_file.exists():
            return True

        with open(self.ledger_file, "r") as f:
            lines = f.readlines()

        for i, line in enumerate(lines):
            entry_data = json.loads(line.strip())

            # Verify hash computation
            if entry_data.get("hash_version", 1) >= 2:
                computed_hash = self._compute_entry_hash(entry_data)
            else:
                computed_hash = self._compute_hash(
                    entry_data["entry_id"],
                    entry_data["previous_hash"],
                    entry_data["amount"]
                )

            if computed_hash != entry_data["current_hash"]:
                print(f"Hash mismatch at entry {i}")
                return False

            # Verify chain linkage
            if i > 0:
                prev_entry = json.loads(lines[i - 1].strip())
                if entry_data["previous_hash"] != prev_entry["current_hash"]:
                    print(f"Chain broken at entry {i}")
                    return False

        return True

    def get_balance(self, session_id: Optional[str] = None) -> Dict[str, float]:
        """
        Get financial balance

        Args:
            session_id: Optional session filter

        Returns:
            Dictionary with costs, revenue, and net profit
        """
        entries = self.get_entries(session_id=session_id)

        verified_costs = sum(abs(e.amount) for e in entries if e.category == "cost" and e.verified)
        verified_revenue = sum(e.amount for e in entries if e.category == "revenue" and e.verified)
        unverified_costs = sum(abs(e.amount) for e in entries if e.category == "cost" and not e.verified)
        unverified_revenue = sum(e.amount for e in entries if e.category == "revenue" and not e.verified)
        net_profit = verified_revenue - verified_costs

        return {
            "total_costs": verified_costs,
            "total_revenue": verified_revenue,
            "unverified_costs": unverified_costs,
            "unverified_revenue": unverified_revenue,
            "net_profit": net_profit,
            "verified": not (unverified_costs or unverified_revenue),
            "roi_percent": (net_profit / verified_costs * 100) if verified_costs > 0 else 0
        }

    def get_component_performance(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance metrics by component

        Returns:
            Dictionary mapping component to performance stats
        """
        entries = self.get_entries()

        component_stats = {}
        for entry in entries:
            if entry.component not in component_stats:
                component_stats[entry.component] = {
                    "total_cost": 0.0,
                    "total_revenue": 0.0,
                    "unverified_cost": 0.0,
                    "unverified_revenue": 0.0,
                    "net_profit": 0.0,
                    "verified": True,
                    "roi_percent": 0.0
                }

            stats = component_stats[entry.component]
            if entry.category == "cost":
                key = "total_cost" if entry.verified else "unverified_cost"
                stats[key] += abs(entry.amount)
            elif entry.category == "revenue":
                key = "total_revenue" if entry.verified else "unverified_revenue"
                stats[key] += entry.amount

        # Calculate derived metrics using verified entries only.
        for component, stats in component_stats.items():
            stats["net_profit"] = stats["total_revenue"] - stats["total_cost"]
            stats["verified"] = stats["unverified_cost"] == 0 and stats["unverified_revenue"] == 0
            if stats["total_cost"] > 0:
                stats["roi_percent"] = (stats["net_profit"] / stats["total_cost"]) * 100

        return component_stats
